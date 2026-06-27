# HCV PRO - Architecture Diagramme Mermaid

## Vue d'Ensemble du Système

```mermaid
graph TB
    %% Frontend Layer
    subgraph "Frontend Layer"
        WebUI[HCV Studio Web UI]
        MobileUI[Mobile Interface]
        API_Client[API Client]
    end

    %% API Gateway
    subgraph "API Gateway Layer"
        Vercel[Vercel Platform]
        Auth[Authentication Service]
        Router[Request Router]
    end

    %% Core Services
    subgraph "Core Services"
        HCV_Engine[HCV16 Compression Engine]
        Video_Decoder[Video Decoder Service]
        Image_Processor[Image Processor]
        Upscaling_Engine[Upscaling Engine]
    end

    %% AI Agent Layer
    subgraph "AI Agent Layer"
        Hermes[Hermes Agent]
        File_Scanner[File Scanner Skill]
        Compression_Analyzer[Compression Analyzer Skill]
        Cloud_Uploader[Cloud Uploader Skill]
        AI_Assistant[AI Assistant]
    end

    %% Mobile Integration
    subgraph "Mobile Integration"
        Mobile_Codec[Mobile Codec Handler]
        Device_Profiles[Device Profiles]
        Media_Scanner[Media Scanner]
        Storage_Optimizer[Storage Optimizer]
    end

    %% Storage Layer
    subgraph "Storage Layer"
        Local_Storage[Local Storage]
        Cloud_Storage[Cloud Storage]
        Compressed_Files[Compressed Files Cache]
        Metadata_DB[Metadata Database]
    end

    %% External Services
    subgraph "External Services"
        OpenAI[OpenAI API]
        Anthropic[Anthropic API]
        AWS[AWS Services]
        CDN[CDN Network]
    end

    %% Connections
    WebUI --> Vercel
    MobileUI --> Vercel
    API_Client --> Vercel
    
    Vercel --> Auth
    Vercel --> Router
    
    Router --> HCV_Engine
    Router --> Video_Decoder
    Router --> Image_Processor
    Router --> Upscaling_Engine
    Router --> Mobile_Codec
    
    HCV_Engine --> Hermes
    Video_Decoder --> Hermes
    Image_Processor --> Hermes
    Mobile_Codec --> Hermes
    
    Hermes --> File_Scanner
    Hermes --> Compression_Analyzer
    Hermes --> Cloud_Uploader
    Hermes --> AI_Assistant
    
    Mobile_Codec --> Device_Profiles
    Mobile_Codec --> Media_Scanner
    Mobile_Codec --> Storage_Optimizer
    
    File_Scanner --> Local_Storage
    Compression_Analyzer --> Metadata_DB
    Cloud_Uploader --> Cloud_Storage
    Storage_Optimizer --> Compressed_Files
    
    AI_Assistant --> OpenAI
    AI_Assistant --> Anthropic
    Cloud_Uploader --> AWS
    Cloud_Storage --> CDN

    %% Styling
    classDef frontend fill:#e1f5fe
    classDef api fill:#f3e5f5
    classDef core fill:#e8f5e8
    classDef ai fill:#fff3e0
    classDef mobile fill:#fce4ec
    classDef storage fill:#f1f8e9
    classDef external fill:#fafafa
    
    class WebUI,MobileUI,API_Client frontend
    class Vercel,Auth,Router api
    class HCV_Engine,Video_Decoder,Image_Processor,Upscaling_Engine core
    class Hermes,File_Scanner,Compression_Analyzer,Cloud_Uploader,AI_Assistant ai
    class Mobile_Codec,Device_Profiles,Media_Scanner,Storage_Optimizer mobile
    class Local_Storage,Cloud_Storage,Compressed_Files,Metadata_DB storage
    class OpenAI,Anthropic,AWS,CDN external
```

## Flux de Compression Mobile

```mermaid
sequenceDiagram
    participant User as Mobile User
    participant MobileUI as Mobile Interface
    participant Hermes as Hermes Agent
    participant Scanner as File Scanner
    participant Codec as HCV Codec
    participant Analyzer as Compression Analyzer
    participant Storage as Storage Manager
    
    User->>MobileUI: Upload Media File
    MobileUI->>Hermes: Request Compression
    Hermes->>Scanner: Scan Media Library
    Scanner-->>Hermes: File List & Metadata
    
    Hermes->>Codec: Analyze File Format
    Codec-->>Hermes: Codec Recommendation
    
    Hermes->>Codec: Compress File
    Codec-->>Hermes: Compressed Data + Stats
    
    Hermes->>Analyzer: Analyze Compression Result
    Analyzer-->>Hermes: Optimization Suggestions
    
    Hermes->>Storage: Store Compressed File
    Storage-->>Hermes: Storage Confirmation
    
    Hermes-->>MobileUI: Compression Complete
    MobileUI-->>User: Results & Suggestions
```

## Architecture des Codecs HCV

```mermaid
graph LR
    subgraph "Input Formats"
        JPEG[JPEG Images]
        PNG[PNG Images]
        MP4[MP4 Videos]
        MOV[MOV Videos]
        H264[H.264 Streams]
        SDI[SDI 4:2:2]
    end

    subgraph "HCV16 Codecs"
        Broadcast[Broadcast Codec<br/>12-bit Grain Synthesis]
        Android[Android Boost<br/>Mobile Optimized]
        Universal[Universal Boost<br/>Multi-format]
        Video[Video Boost<br/>Streaming Optimized]
    end

    subgraph "Output Formats"
        HCV16[HCV16 Files]
        WebP[WebP Images]
        MP4_Opt[Optimized MP4]
        H265[H.265 Streams]
    end

    JPEG --> Android
    PNG --> Universal
    MP4 --> Video
    MOV --> Video
    H264 --> Broadcast
    SDI --> Broadcast

    Android --> HCV16
    Universal --> WebP
    Video --> MP4_Opt
    Broadcast --> H265

    classDef input fill:#e3f2fd
    classDef codec fill:#f1f8e9
    classDef output fill:#fff3e0
    
    class JPEG,PNG,MP4,MOV,H264,SDI input
    class Broadcast,Android,Universal,Video codec
    class HCV16,WebP,MP4_Opt,H265 output
```

## Intégration Hermes Agent

```mermaid
mindmap
  root((Hermes Agent))
    Core Features
      CLI Interface
      Messaging Gateway
      Skills System
      Memory Management
    Integration Points
      HCV Engine
      Mobile Codecs
      Cloud Storage
      AI Services
    Skills
      file-scanner
      compression-analyzer
      cloud-uploader
      assistant-creator
    Platforms
      Linux
      macOS
      WSL2
      Android/Termux
    External APIs
      OpenAI
      Anthropic
      AWS
      Google Cloud
```

## Déploiement Cloud

```mermaid
graph TB
    subgraph "Development Environment"
        Dev_Local[Local Development]
        Dev_Docker[Docker Container]
        Dev_Tests[Automated Tests]
    end

    subgraph "Staging Environment"
        Staging_Vercel[Vercel Preview]
        Staging_AWS[AWS Staging]
        Staging_DB[Staging Database]
    end

    subgraph "Production Environment"
        Prod_Vercel[Vercel Production]
        Prod_AWS[AWS Production]
        Prod_CDN[CloudFront CDN]
        Prod_S3[S3 Storage]
    end

    subgraph "Monitoring & Analytics"
        Logs[Logging Service]
        Metrics[Performance Metrics]
        Alerts[Alert System]
        Analytics[Usage Analytics]
    end

    Dev_Local --> Staging_Vercel
    Dev_Docker --> Staging_AWS
    Dev_Tests --> Staging_DB

    Staging_Vercel --> Prod_Vercel
    Staging_AWS --> Prod_AWS
    Staging_DB --> Prod_S3

    Prod_Vercel --> Prod_CDN
    Prod_AWS --> Prod_S3

    Prod_Vercel --> Logs
    Prod_AWS --> Metrics
    Prod_CDN --> Alerts
    Prod_S3 --> Analytics

    classDef dev fill:#e8f5e8
    classDef staging fill:#fff3e0
    classDef prod fill:#ffebee
    classDef monitor fill:#f3e5f5
    
    class Dev_Local,Dev_Docker,Dev_Tests dev
    class Staging_Vercel,Staging_AWS,Staging_DB staging
    class Prod_Vercel,Prod_AWS,Prod_CDN,Prod_S3 prod
    class Logs,Metrics,Alerts,Analytics monitor
```

## Flux de Données Mobile

```mermaid
flowchart TD
    Start([Mobile User]) --> Upload[Upload Media]
    Upload --> Detect{Detect Device Type}
    
    Detect --> Low[Low-end Device]
    Detect --> Mid[Mid-range Device]
    Detect --> High[High-end Device]
    Detect --> Aug[Augmented Device]
    
    Low --> AndroidCodec[Android Boost Codec]
    Mid --> UniversalCodec[Universal Boost Codec]
    High --> BroadcastCodec[Broadcast Codec]
    Aug --> AdaptiveCodec[Adaptive Codec]
    
    AndroidCodec --> Compress[Compress with Quality: 60%]
    UniversalCodec --> CompressMid[Compress with Quality: 75%]
    BroadcastCodec --> CompressHigh[Compress with Quality: 85%]
    AdaptiveCodec --> CompressAdapt[Adaptive Compression]
    
    Compress --> Analyze[Hermes Analysis]
    CompressMid --> Analyze
    CompressHigh --> Analyze
    CompressAdapt --> Analyze
    
    Analyze --> Suggest[AI Suggestions]
    Suggest --> Store[Store Locally]
    Suggest --> Backup[Cloud Backup]
    
    Store --> Complete[Compression Complete]
    Backup --> Complete
    
    Complete --> End([User Notified])

    classDef process fill:#e1f5fe
    classDef decision fill:#fff3e0
    classDef codec fill:#e8f5e8
    classDef storage fill:#f3e5f5
    
    class Upload,Detect,Analyze,Suggest,Store,Backup,Complete process
    class Low,Mid,High,Aug decision
    class AndroidCodec,UniversalCodec,BroadcastCodec,AdaptiveCodec codec
    class Compress,CompressMid,CompressHigh,CompressAdapt storage
```

## Architecture de Sécurité

```mermaid
graph TB
    subgraph "Security Layers"
        subgraph "Authentication"
            JWT[JWT Tokens]
            OAuth[OAuth 2.0]
            API_Keys[API Keys]
        end
        
        subgraph "Authorization"
            RBAC[Role-Based Access]
            Permissions[File Permissions]
            Rate_Limit[Rate Limiting]
        end
        
        subgraph "Data Protection"
            Encryption[Encryption at Rest]
            TLS[TLS in Transit]
            Hashing[Password Hashing]
        end
        
        subgraph "Monitoring"
            Audit_Logs[Audit Logs]
            Intrusion[Intrusion Detection]
            Anomaly[Anomaly Detection]
        end
    end

    subgraph "Protected Resources"
        API_Endpoints[API Endpoints]
        User_Data[User Data]
        Media_Files[Media Files]
        Config[Configuration]
    end

    JWT --> API_Endpoints
    OAuth --> User_Data
    API_Keys --> Media_Files
    
    RBAC --> API_Endpoints
    Permissions --> User_Data
    Rate_Limit --> Media_Files
    
    Encryption --> Config
    TLS --> API_Endpoints
    Hashing --> User_Data
    
    Audit_Logs --> API_Endpoints
    Intrusion --> Media_Files
    Anomaly --> User_Data

    classDef auth fill:#e3f2fd
    classDef authz fill:#e8f5e8
    classDef crypto fill:#fff3e0
    classDef monitor fill:#f3e5f5
    classDef resource fill:#ffebee
    
    class JWT,OAuth,API_Keys auth
    class RBAC,Permissions,Rate_Limit authz
    class Encryption,TLS,Hashing crypto
    class Audit_Logs,Intrusion,Anomaly monitor
    class API_Endpoints,User_Data,Media_Files,Config resource
```

## Performance Monitoring

```mermaid
graph LR
    subgraph "Metrics Collection"
        CPU[CPU Usage]
        Memory[Memory Usage]
        Disk[Disk I/O]
        Network[Network I/O]
        Compression[Compression Ratio]
        Latency[Response Time]
    end

    subgraph "Processing"
        Aggregator[Metrics Aggregator]
        Analyzer[Performance Analyzer]
        Alert_Engine[Alert Engine]
    end

    subgraph "Visualization"
        Dashboard[Performance Dashboard]
        Reports[Automated Reports]
        Alerts[Alert Notifications]
    end

    CPU --> Aggregator
    Memory --> Aggregator
    Disk --> Aggregator
    Network --> Aggregator
    Compression --> Aggregator
    Latency --> Aggregator

    Aggregator --> Analyzer
    Analyzer --> Alert_Engine

    Analyzer --> Dashboard
    Alert_Engine --> Alerts
    Analyzer --> Reports

    classDef collection fill:#e1f5fe
    classDef processing fill:#e8f5e8
    classDef viz fill:#fff3e0
    
    class CPU,Memory,Disk,Network,Compression,Latency collection
    class Aggregator,Analyzer,Alert_Engine processing
    class Dashboard,Reports,Alerts viz
```

---

## Légende

- **Bleu** : Frontend et interfaces utilisateur
- **Violet** : API et services de routage
- **Vert** : Moteurs de compression et traitement
- **Orange** : Agents IA et compétences
- **Rose** : Intégration mobile
- **Vert clair** : Stockage et persistance
- **Gris** : Services externes

Ces diagrammes illustrent l'architecture complète du système HCV PRO avec l'intégration Hermes Agent, montrant les flux de données, les dépendances et les interactions entre les différents composants.
