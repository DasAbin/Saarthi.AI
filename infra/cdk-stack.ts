/**
 * AWS CDK Infrastructure as Code for Saarthi.AI
 * 
 * This stack creates:
 * - API Gateway
 * - Lambda functions for each endpoint
 * - DynamoDB table for vector storage
 * - S3 buckets for PDFs and embeddings
 * - IAM roles with least privilege
 * - CloudWatch logs
 */

import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as logs from 'aws-cdk-lib/aws-logs';
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

    // S3 bucket for conversation logs
    const conversationsBucket = new s3.Bucket(this, 'SaarthiConversationsBucket', {
      bucketName: `saarthi-conversations-${this.account}-${this.region}`,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
      encryption: s3.BucketEncryption.S3_MANAGED,
      lifecycleRules: [{
        expiration: cdk.Duration.days(365),
      }],
    });

    // DynamoDB Table for Vector Storage (DocumentChunks)
    const vectorsTable = new dynamodb.Table(this, 'SaarthiVectorsTable', {
      tableName: 'saarthi-vectors',
      partitionKey: { name: 'chunk_id', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'metadata', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
      pointInTimeRecoverySpecification: {
        pointInTimeRecoveryEnabled: true,
      },
    });

    // DynamoDB table for query cache
    const queryCacheTable = new dynamodb.Table(this, 'SaarthiQueryCacheTable', {
      tableName: 'saarthi-query-cache',
      partitionKey: { name: 'query_hash', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
    });

    // Lambda Execution Role
    const lambdaRole = new iam.Role(this, 'LambdaExecutionRole', {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
      ],
    });

    // Grant Bedrock permissions (allow any Bedrock model so TEXT_MODEL_ID can be changed freely)
    lambdaRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'bedrock:InvokeModel',
        'bedrock:Converse',
        'bedrock:ConverseStream',
        'bedrock:InvokeModelWithResponseStream',
      ],
      resources: ['*'],
    }));

    // Grant S3 permissions
    pdfBucket.grantReadWrite(lambdaRole);
    embeddingsBucket.grantReadWrite(lambdaRole);
    tempAudioBucket.grantReadWrite(lambdaRole);
    conversationsBucket.grantReadWrite(lambdaRole);

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

    // Grant DynamoDB permissions
    vectorsTable.grantReadWriteData(lambdaRole);
    queryCacheTable.grantReadWriteData(lambdaRole);

    // Lambda Functions
    const commonLambdaProps = {
      runtime: lambda.Runtime.PYTHON_3_12,
      role: lambdaRole,
      timeout: cdk.Duration.minutes(5),
      memorySize: 512,
      environment: {
        PDF_BUCKET: pdfBucket.bucketName,
        EMBEDDINGS_BUCKET: embeddingsBucket.bucketName,
        TEMP_AUDIO_BUCKET: tempAudioBucket.bucketName,
        DYNAMODB_TABLE: vectorsTable.tableName,
        CONVERSATIONS_BUCKET: conversationsBucket.bucketName,
        QUERY_CACHE_TABLE: queryCacheTable.tableName,
        // Optional: override these at deploy-time or in the Lambda console
        // when AWS retires or replaces a specific model version.
        // Recommended defaults for ap-south-1:
        // - Nova Micro via APAC inference profile (Converse API)
        // - Titan Embeddings (InvokeModel API)
        TEXT_MODEL_ID: process.env.TEXT_MODEL_ID ?? 'apac.amazon.nova-micro-v1:0',
        EMBEDDING_MODEL_ID: process.env.EMBEDDING_MODEL_ID ?? 'amazon.titan-embed-text-v2:0',
      },
      logRetention: logs.RetentionDays.ONE_WEEK,
    };

    const ragQueryLambda = new lambda.Function(this, 'RagQueryLambda', {
      ...commonLambdaProps,
      functionName: 'saarthi-rag-query',
      // Package the entire backend so shared utils are available to all Lambdas
      code: lambda.Code.fromAsset('../backend'),
      handler: 'lambdas/rag_query/handler.handler',
      memorySize: 1024, // More memory for RAG processing
    });

    const pdfProcessLambda = new lambda.Function(this, 'PdfProcessLambda', {
      ...commonLambdaProps,
      functionName: 'saarthi-document-process',
      code: lambda.Code.fromAsset('../backend'),
      handler: 'lambdas/pdf_process/handler.handler',
      memorySize: 2048, // More memory for PDF processing
      timeout: cdk.Duration.minutes(10),
    });

    const recommendSchemesLambda = new lambda.Function(this, 'RecommendSchemesLambda', {
      ...commonLambdaProps,
      functionName: 'saarthi-recommend-schemes',
      code: lambda.Code.fromAsset('../backend'),
      handler: 'lambdas/recommend_schemes/handler.handler',
    });

    const sttHandlerLambda = new lambda.Function(this, 'SttHandlerLambda', {
      ...commonLambdaProps,
      functionName: 'saarthi-stt-handler',
      code: lambda.Code.fromAsset('../backend'),
      handler: 'lambdas/stt_handler/handler.handler',
      timeout: cdk.Duration.minutes(10), // Transcribe can take time
    });

    const ttsHandlerLambda = new lambda.Function(this, 'TtsHandlerLambda', {
      ...commonLambdaProps,
      functionName: 'saarthi-tts-handler',
      code: lambda.Code.fromAsset('../backend'),
      handler: 'lambdas/tts_handler/handler.handler',
    });

    const grievanceHandlerLambda = new lambda.Function(this, 'GrievanceHandlerLambda', {
      ...commonLambdaProps,
      functionName: 'saarthi-grievance-handler',
      code: lambda.Code.fromAsset('../backend'),
      handler: 'lambdas/grievance_handler/handler.handler',
    });

    const uploadUrlLambda = new lambda.Function(this, 'UploadUrlLambda', {
      ...commonLambdaProps,
      functionName: 'saarthi-upload-url',
      code: lambda.Code.fromAsset('../backend'),
      handler: 'lambdas/upload_url/handler.handler',
      memorySize: 256,
    });

    const healthLambda = new lambda.Function(this, 'HealthLambda', {
      ...commonLambdaProps,
      functionName: 'saarthi-health',
      code: lambda.Code.fromAsset('../backend'),
      handler: 'lambdas/health/handler.handler',
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
    const uploadUrlIntegration = new apigateway.LambdaIntegration(uploadUrlLambda);
    const recommendIntegration = new apigateway.LambdaIntegration(recommendSchemesLambda);
    const sttIntegration = new apigateway.LambdaIntegration(sttHandlerLambda);
    const ttsIntegration = new apigateway.LambdaIntegration(ttsHandlerLambda);
    const grievanceIntegration = new apigateway.LambdaIntegration(grievanceHandlerLambda);
    const healthIntegration = new apigateway.LambdaIntegration(healthLambda);

    // API Routes
    api.root.addResource('health').addMethod('GET', healthIntegration);
    api.root.addResource('query').addMethod('POST', queryIntegration);

    // Document processing routes
    const pdfResource = api.root.addResource('pdf');
    pdfResource.addMethod('POST', pdfIntegration);

    // New upload-url route for presigned S3 uploads
    api.root.addResource('upload-url').addMethod('POST', uploadUrlIntegration);
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

    new cdk.CfnOutput(this, 'DynamoDBTableName', {
      value: vectorsTable.tableName,
      description: 'DynamoDB Table for Vector Storage',
    });

    new cdk.CfnOutput(this, 'QueryCacheTableName', {
      value: queryCacheTable.tableName,
      description: 'DynamoDB Table for Query Cache',
    });
  }
}
