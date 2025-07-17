The connection string parameters for UberConnection are:

        [Description("Application name used to identify to UNIQE server with")]
        public string Application { get; set; }
        
        [Description("User Authentication Mode (IWA, UNP or UPWD)")]
        public AuthMode Authentication { get; set; }
        
        [Description("Chunk size in bytes for each chunk of data sent by server")]
        public int ChunkSizeInBytes { get; set; }
        
        [Description("Data accessor to use on the server side when executing the query (e.g., default, ODP, SQL, DevArtODP)")]
        public string DataAccessor { get; set; }
        
        [Description("UNIQE data source to query")]
        public string DataSource { get; set; }
        
        [Description("Dump SQLs to log file before executing")]
        public bool DumpSQL { get; set; }
        
        [Description("Enable compression for data returned by server")]
        public bool EnableCompression { get; set; }
        
        [DefaultValue(true)]
        [Description("Enable sequential mode for writes")]
        public bool EnableSequentialModeForWrites { get; set; }
        
        [DefaultValue(true)]
        [Description("Enable transaction mode for Writes")]
        public bool EnableTransactionModeForWrites { get; set; }
        
        [DefaultValue(false)]
        [Description("Enable write support for the data-source")]
        public bool EnableWrites { get; set; }
        
        [Description("Get only the schema table for the output query table")]
        [DefaultValue(false)]
        public bool GetSchemaTable { get; set; }
        
        [Description("Ignore order by/group by when splitting query")]
        public bool IgnoreOrderBy { get; set; }
        
        [Description("Maximum number of child threads for query splitting")]
        public int MaxNumOfChildThreads { get; set; }
        
        [Description("Client-side meta-data")]
        public string MetaData { get; set; }
        
        [DefaultValue(604800)]
        [Description("Minimum number of seconds for breaking date-time range in queries")]
        public long MinThresholdPeriodInSecondsForQueryBreakUp { get; set; }
        
        [DefaultValue("")]
        [Description("User password for UPWD authentication")]
        public string Password { get; set; }
        
        [Description("Default UNIQE Server to connect to (leave it empty or BEST to auto-route)")]
        [DefaultValue("")]
        public string Site { get; set; }
        
        [Description("Transaction time-out in seconds")]
        [DefaultValue(7200)]
        public int TimeOutInSeconds { get; set; }
        
        [DefaultValue("")]
        [Description("User ID for authentication")]
        public string UserId { get; set; }
