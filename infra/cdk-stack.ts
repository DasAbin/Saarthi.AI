/**
 * AWS CDK Infrastructure as Code for Saarthi.AI
 * 
 * This stack creates:
 * - API Gateway (with rate limiting and proper CORS)
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
      bucketName: `saarthi-pdfs-${this.account}-${this.region}-v2`,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
      encryption: s3.BucketEncryption.S3_MANAGED,
      versioned: true,
      lifecycleRules: [{
        expiration: cdk.Duration.days(365),
      }],
      cors: [
        {
          allowedMethods: [s3.HttpMethods.GET, s3.HttpMethods.POST, s3.HttpMethods.PUT, s3.HttpMethods.DELETE],
          allowedOrigins: ['*'],
          allowedHeaders: ['*'],
          maxAge: 3000,
        },
      ],
    });

    const embeddingsBucket = new s3.Bucket(this, 'SaarthiEmbeddingsBucket', {
      bucketName: `saarthi-embeddings-${this.account}-${this.region}-v2`,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
      encryption: s3.BucketEncryption.S3_MANAGED,
    });

    const tempAudioBucket = new s3.Bucket(this, 'SaarthiTempAudioBucket', {
      bucketName: `saarthi-temp-audio-${this.account}-${this.region}-v2`,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      encryption: s3.BucketEncryption.S3_MANAGED,
      lifecycleRules: [{
        expiration: cdk.Duration.days(1), // Auto-delete after 1 day
      }],
      cors: [
        {
          allowedMethods: [s3.HttpMethods.GET, s3.HttpMethods.POST, s3.HttpMethods.PUT, s3.HttpMethods.DELETE],
          allowedOrigins: ['*'],
          allowedHeaders: ['*'],
          maxAge: 3000,
        },
      ],
    });

    // S3 bucket for conversation logs (Legacy, migrating to DynamoDB)
    const conversationsBucket = new s3.Bucket(this, 'SaarthiConversationsBucket', {
      bucketName: `saarthi-conversations-${this.account}-${this.region}-v2`,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
      encryption: s3.BucketEncryption.S3_MANAGED,
      lifecycleRules: [{
        expiration: cdk.Duration.days(365),
      }],
    });

    // DynamoDB Table for Vector Storage (DocumentChunks)
    const vectorsTable = new dynamodb.Table(this, 'SaarthiVectorsTable', {
      tableName: 'saarthi-vectors-v2',
      partitionKey: { name: 'chunk_id', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
      pointInTimeRecoverySpecification: {
        pointInTimeRecoveryEnabled: true,
      },
    });

    // DynamoDB table for query cache
    const queryCacheTable = new dynamodb.Table(this, 'SaarthiQueryCacheTable', {
      tableName: 'saarthi-query-cache-v2',
      partitionKey: { name: 'query_hash', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
      timeToLiveAttribute: 'expires_at',
    });

    // DynamoDB table for conversation sessions (atomic per-event writes, replaces S3)
    const sessionsTable = new dynamodb.Table(this, 'SaarthiSessionsTable', {
      tableName: 'saarthi-sessions-v2',
      partitionKey: { name: 'session_id', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'timestamp', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
      timeToLiveAttribute: 'expires_at',
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

    // Grant Translate permissions
    lambdaRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'translate:TranslateText',
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
    sessionsTable.grantReadWriteData(lambdaRole);

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
        TEXT_MODEL_ID: process.env.TEXT_MODEL_ID ?? 'apac.amazon.nova-micro-v1:0',
        EMBEDDING_MODEL_ID: process.env.EMBEDDING_MODEL_ID ?? 'amazon.titan-embed-text-v2:0',
        SESSIONS_TABLE: sessionsTable.tableName,
        CACHE_TTL_SECONDS: '86400',
      },
      logRetention: logs.RetentionDays.ONE_WEEK,
    };

    const ragQueryLambda = new lambda.Function(this, 'RagQueryLambda', {
      ...commonLambdaProps,
      functionName: 'saarthi-rag-query-v2',
      // Package the entire backend so shared utils are available to all Lambdas
      code: lambda.Code.fromAsset('../backend'),
      handler: 'lambdas/rag_query/handler.handler',
      memorySize: 1024, // More memory for RAG processing
    });

    const pdfProcessLambda = new lambda.Function(this, 'PdfProcessLambda', {
      ...commonLambdaProps,
      functionName: 'saarthi-document-process-v2',
      code: lambda.Code.fromAsset('../backend'),
      handler: 'lambdas/pdf_process/handler.handler',
      memorySize: 2048, // More memory for PDF processing
      timeout: cdk.Duration.minutes(10),
    });

    const pdfStatusLambda = new lambda.Function(this, 'PdfStatusLambda', {
      ...commonLambdaProps,
      functionName: 'saarthi-document-status-v2',
      code: lambda.Code.fromAsset('../backend'),
      handler: 'lambdas/pdf_status/handler.handler',
      memorySize: 1024,
      timeout: cdk.Duration.minutes(5),
    });

    const recommendSchemesLambda = new lambda.Function(this, 'RecommendSchemesLambda', {
      ...commonLambdaProps,
      functionName: 'saarthi-recommend-schemes-v2',
      code: lambda.Code.fromAsset('../backend'),
      handler: 'lambdas/recommend_schemes/handler.handler',
    });

    const sttHandlerLambda = new lambda.Function(this, 'SttHandlerLambda', {
      ...commonLambdaProps,
      functionName: 'saarthi-stt-handler-v2',
      code: lambda.Code.fromAsset('../backend'),
      handler: 'lambdas/stt_handler/handler.handler',
      timeout: cdk.Duration.minutes(10), // Transcribe can take time
    });

    const ttsHandlerLambda = new lambda.Function(this, 'TtsHandlerLambda', {
      ...commonLambdaProps,
      functionName: 'saarthi-tts-handler-v2',
      code: lambda.Code.fromAsset('../backend'),
      handler: 'lambdas/tts_handler/handler.handler',
    });

    const grievanceHandlerLambda = new lambda.Function(this, 'GrievanceHandlerLambda', {
      ...commonLambdaProps,
      functionName: 'saarthi-grievance-handler-v2',
      code: lambda.Code.fromAsset('../backend'),
      handler: 'lambdas/grievance_handler/handler.handler',
    });

    const uploadUrlLambda = new lambda.Function(this, 'UploadUrlLambda', {
      ...commonLambdaProps,
      functionName: 'saarthi-upload-url-v2',
      code: lambda.Code.fromAsset('../backend'),
      handler: 'lambdas/upload_url/handler.handler',
      memorySize: 256,
    });

    const healthLambda = new lambda.Function(this, 'HealthLambda', {
      ...commonLambdaProps,
      functionName: 'saarthi-health-v2',
      code: lambda.Code.fromAsset('../backend'),
      handler: 'lambdas/health/handler.handler',
      memorySize: 128,
    });

    // API Gateway
    const api = new apigateway.RestApi(this, 'SaarthiApi', {
      restApiName: 'Saarthi.AI API v2',
      description: 'API Gateway for Saarthi.AI',
      deployOptions: {
        stageName: 'prod',
        throttlingRateLimit: 50,
        throttlingBurstLimit: 100,
        loggingLevel: apigateway.MethodLoggingLevel.INFO,
        metricsEnabled: true,
      },
      defaultCorsPreflightOptions: {
        allowOrigins: apigateway.Cors.ALL_ORIGINS,
        allowMethods: apigateway.Cors.ALL_METHODS,
        allowHeaders: ['Content-Type', 'X-Amz-Date', 'Authorization', 'X-Api-Key', 'X-Session-Id', 'X-Language-Code'],
      },
      binaryMediaTypes: ['application/pdf', 'audio/*', 'multipart/form-data'],
    });

    // API Gateway Integrations
    const queryIntegration = new apigateway.LambdaIntegration(ragQueryLambda);
    const pdfIntegration = new apigateway.LambdaIntegration(pdfProcessLambda);
    const pdfStatusIntegration = new apigateway.LambdaIntegration(pdfStatusLambda);
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
    const pdfStatusResource = pdfResource.addResource('{document_id}');
    pdfStatusResource.addMethod('GET', pdfStatusIntegration);

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
      description: 'Set as NEXT_PUBLIC_API_GATEWAY_URL in frontend environment variables',
      exportName: 'SaarthiApiUrlV2',
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
