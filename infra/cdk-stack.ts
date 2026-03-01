/**
 * AWS CDK Infrastructure as Code for Saarthi.AI
 * 
 * This stack creates:
 * - API Gateway
 * - Lambda functions for each endpoint
 * - OpenSearch Serverless collection and index
 * - S3 buckets for PDFs and embeddings
 * - IAM roles with least privilege
 * - CloudWatch logs
 */

import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as opensearchserverless from 'aws-cdk-lib/aws-opensearchserverless';
import { Construct } from 'constructs';

export class SaarthiAiStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // S3 Buckets
    const pdfBucket = new s3.Bucket(this, 'SaarthiPdfBucket', {
      bucketName: `saarthi-pdfs-${this.account}-${this.region}`,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
      encryption: s3.BucketEncryption.S3_MANAGED,
      versioned: true,
      lifecycleRules: [{
        expiration: cdk.Duration.days(365),
      }],
    });

    const embeddingsBucket = new s3.Bucket(this, 'SaarthiEmbeddingsBucket', {
      bucketName: `saarthi-embeddings-${this.account}-${this.region}`,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
      encryption: s3.BucketEncryption.S3_MANAGED,
    });

    const tempAudioBucket = new s3.Bucket(this, 'SaarthiTempAudioBucket', {
      bucketName: `saarthi-temp-audio-${this.account}-${this.region}`,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      encryption: s3.BucketEncryption.S3_MANAGED,
      lifecycleRules: [{
        expiration: cdk.Duration.days(1), // Auto-delete after 1 day
      }],
    });

    // OpenSearch Serverless Collection
    const collection = new opensearchserverless.CfnCollection(this, 'SaarthiCollection', {
      name: 'saarthi-collection',
      type: 'VECTORSEARCH',
      description: 'Vector search collection for Saarthi.AI RAG',
    });

    // OpenSearch Serverless Index
    const index = new opensearchserverless.CfnIndex(this, 'SaarthiIndex', {
      collectionName: collection.name!,
      name: 'saarthi-index',
      type: 'vectorsearch',
    });

    // Lambda Execution Role
    const lambdaRole = new iam.Role(this, 'LambdaExecutionRole', {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
      ],
    });

    // Grant Bedrock permissions
    lambdaRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'bedrock:InvokeModel',
        'bedrock:InvokeModelWithResponseStream',
      ],
      resources: [
        `arn:aws:bedrock:${this.region}::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0`,
        `arn:aws:bedrock:${this.region}::foundation-model/amazon.titan-embed-text-v1`,
      ],
    }));

    // Grant S3 permissions
    pdfBucket.grantReadWrite(lambdaRole);
    embeddingsBucket.grantReadWrite(lambdaRole);
    tempAudioBucket.grantReadWrite(lambdaRole);

    // Grant Textract permissions
    lambdaRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'textract:DetectDocumentText',
        'textract:AnalyzeDocument',
        'textract:StartDocumentTextDetection',
        'textract:GetDocumentTextDetection',
      ],
      resources: ['*'],
    }));

    // Grant Transcribe permissions
    lambdaRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'transcribe:StartTranscriptionJob',
        'transcribe:GetTranscriptionJob',
        'transcribe:DeleteTranscriptionJob',
      ],
      resources: ['*'],
    }));

    // Grant Polly permissions
    lambdaRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'polly:SynthesizeSpeech',
      ],
      resources: ['*'],
    }));

    // Grant OpenSearch Serverless permissions
    lambdaRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'aoss:APIAccessAll',
      ],
      resources: [collection.attrArn],
    }));

    // Lambda Functions
    const commonLambdaProps = {
      runtime: lambda.Runtime.PYTHON_3_12,
      role: lambdaRole,
      timeout: cdk.Duration.minutes(5),
      memorySize: 512,
      environment: {
        AWS_REGION: this.region,
        PDF_BUCKET: pdfBucket.bucketName,
        EMBEDDINGS_BUCKET: embeddingsBucket.bucketName,
        TEMP_AUDIO_BUCKET: tempAudioBucket.bucketName,
        OPENSEARCH_ENDPOINT: collection.attrCollectionEndpoint || '',
        OPENSEARCH_INDEX: index.name!,
        OPENSEARCH_COLLECTION: collection.name!,
      },
      logRetention: logs.RetentionDays.ONE_WEEK,
    };

    const ragQueryLambda = new lambda.Function(this, 'RagQueryLambda', {
      ...commonLambdaProps,
      functionName: 'saarthi-rag-query',
      code: lambda.Code.fromAsset('backend/lambdas/rag_query'),
      handler: 'handler.handler',
      memorySize: 1024, // More memory for RAG processing
    });

    const pdfProcessLambda = new lambda.Function(this, 'PdfProcessLambda', {
      ...commonLambdaProps,
      functionName: 'saarthi-pdf-process',
      code: lambda.Code.fromAsset('backend/lambdas/pdf_process'),
      handler: 'handler.handler',
      memorySize: 2048, // More memory for PDF processing
      timeout: cdk.Duration.minutes(10),
    });

    const recommendSchemesLambda = new lambda.Function(this, 'RecommendSchemesLambda', {
      ...commonLambdaProps,
      functionName: 'saarthi-recommend-schemes',
      code: lambda.Code.fromAsset('backend/lambdas/recommend_schemes'),
      handler: 'handler.handler',
    });

    const sttHandlerLambda = new lambda.Function(this, 'SttHandlerLambda', {
      ...commonLambdaProps,
      functionName: 'saarthi-stt-handler',
      code: lambda.Code.fromAsset('backend/lambdas/stt_handler'),
      handler: 'handler.handler',
      timeout: cdk.Duration.minutes(10), // Transcribe can take time
    });

    const ttsHandlerLambda = new lambda.Function(this, 'TtsHandlerLambda', {
      ...commonLambdaProps,
      functionName: 'saarthi-tts-handler',
      code: lambda.Code.fromAsset('backend/lambdas/tts_handler'),
      handler: 'handler.handler',
    });

    const grievanceHandlerLambda = new lambda.Function(this, 'GrievanceHandlerLambda', {
      ...commonLambdaProps,
      functionName: 'saarthi-grievance-handler',
      code: lambda.Code.fromAsset('backend/lambdas/grievance_handler'),
      handler: 'handler.handler',
    });

    const healthLambda = new lambda.Function(this, 'HealthLambda', {
      ...commonLambdaProps,
      functionName: 'saarthi-health',
      code: lambda.Code.fromAsset('backend/lambdas/health'),
      handler: 'handler.handler',
      memorySize: 128,
    });

    // API Gateway
    const api = new apigateway.RestApi(this, 'SaarthiApi', {
      restApiName: 'Saarthi.AI API',
      description: 'API Gateway for Saarthi.AI',
      defaultCorsPreflightOptions: {
        allowOrigins: apigateway.Cors.ALL_ORIGINS,
        allowMethods: apigateway.Cors.ALL_METHODS,
        allowHeaders: ['Content-Type', 'X-Amz-Date', 'Authorization', 'X-Api-Key'],
      },
      binaryMediaTypes: ['application/pdf', 'audio/*', 'multipart/form-data'],
    });

    // API Gateway Integrations
    const queryIntegration = new apigateway.LambdaIntegration(ragQueryLambda);
    const pdfIntegration = new apigateway.LambdaIntegration(pdfProcessLambda);
    const recommendIntegration = new apigateway.LambdaIntegration(recommendSchemesLambda);
    const sttIntegration = new apigateway.LambdaIntegration(sttHandlerLambda);
    const ttsIntegration = new apigateway.LambdaIntegration(ttsHandlerLambda);
    const grievanceIntegration = new apigateway.LambdaIntegration(grievanceHandlerLambda);
    const healthIntegration = new apigateway.LambdaIntegration(healthLambda);

    // API Routes
    api.root.addResource('health').addMethod('GET', healthIntegration);
    api.root.addResource('query').addMethod('POST', queryIntegration);
    api.root.addResource('pdf').addMethod('POST', pdfIntegration);
    api.root.addResource('recommend').addMethod('POST', recommendIntegration);
    
    const voiceResource = api.root.addResource('voice');
    voiceResource.addResource('stt').addMethod('POST', sttIntegration);
    voiceResource.addResource('tts').addMethod('POST', ttsIntegration);
    
    api.root.addResource('grievance').addMethod('POST', grievanceIntegration);

    // Outputs
    new cdk.CfnOutput(this, 'ApiGatewayUrl', {
      value: api.url,
      description: 'API Gateway URL',
    });

    new cdk.CfnOutput(this, 'PdfBucketName', {
      value: pdfBucket.bucketName,
      description: 'PDF Storage Bucket',
    });

    new cdk.CfnOutput(this, 'OpenSearchCollectionEndpoint', {
      value: collection.attrCollectionEndpoint || '',
      description: 'OpenSearch Serverless Collection Endpoint',
    });
  }
}
