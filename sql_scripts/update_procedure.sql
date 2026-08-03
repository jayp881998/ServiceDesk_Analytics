USE [zendesklog]
GO
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

-- Create a new stored procedure
Alter PROCEDURE [UpdateProcedure]
    @TicketJsonFilePath NVARCHAR(MAX),
	@UserJsonFilePath NVARCHAR(MAX)
AS
BEGIN

-- Declare variables to hold the JSON content
DECLARE @JSON NVARCHAR(MAX);
DECLARE @JSONUsers NVARCHAR(MAX);
DECLARE @RecordsProcessed INT = 0;

-- Load JSON data from the Tickets file
SELECT @JSON = BulkColumn
FROM OPENROWSET (BULK '<OUTPUT_DIR>\ZendeskTickets.json', SINGLE_CLOB) AS import;

-- Load JSON data from the Users file
SELECT @JSONUsers = BulkColumn
FROM OPENROWSET (BULK '<OUTPUT_DIR>\ZendeskUsers.json', SINGLE_CLOB) AS importUsers;

-- Check if both JSON files are valid
IF (ISJSON(@JSON) = 1) AND (ISJSON(@JSONUsers) = 1)
    PRINT 'Both JSON files are valid';
ELSE

BEGIN
    PRINT 'Error in one or both JSON formats';
    RETURN;
END;
	
    -- Drop the existing table if it exists
    IF OBJECT_ID('dbo.Ticket_Metrics', 'U') IS NOT NULL
    BEGIN
        DROP TABLE dbo.Ticket_Metrics;
    END;
	IF OBJECT_ID('dbo.Tags', 'U') IS NOT NULL 
	BEGIN
		DROP TABLE dbo.Tags;
	END;
	IF OBJECT_ID('dbo.Via', 'U') IS NOT NULL
    BEGIN
        DROP TABLE dbo.Via;
    END;
	IF OBJECT_ID('dbo.Tickets', 'U') IS NOT NULL
    BEGIN
        DROP TABLE dbo.Tickets;
    END;
	IF OBJECT_ID('dbo.Users', 'U') IS NOT NULL
	BEGIN
		DROP TABLE dbo.Users;
	END;

-- Create the Tickets table
CREATE TABLE Tickets (
    [Id] INT PRIMARY KEY,
    [Url] NVARCHAR(255),
    [External Id] NVARCHAR(255),
    [Created At] DATETIME2,
    [Updated At] DATETIME2,
    [Generated Timestamp] BIGINT,
    [Type] NVARCHAR(50),
    [Subject] NVARCHAR(255),
    [Raw Subject] NVARCHAR(255),
    [Description] NVARCHAR(MAX),
    [Priority] NVARCHAR(50),
    [Status] NVARCHAR(50),
    [Recipient] NVARCHAR(255),
    [Requester Id] BIGINT,
    [Submitter Id] BIGINT,
    [Assignee Id] BIGINT,
    [Organization Id] BIGINT,
    [Group Id] BIGINT,
    [Forum Topic Id] BIGINT,
    [Problem Id] BIGINT,
    [Has Incidents] BIT,
    [Is Public] BIT,
    [Due At] DATETIME2 NULL,
    [Custom Status Id] BIGINT,
    [Brand Id] BIGINT,
    [Allow Channelback] BIT,
    [Allow Attachments] BIT,
    [From Messaging Channel] BIT
);

-- Insert into the Tickets table
INSERT INTO Tickets 
SELECT 
    [id],
    [url],
    [external_id],
    [created_at],
    [updated_at],
    [generated_timestamp],
    [type],
    [subject],
    [raw_subject],
    [description],
    [priority],
    [status],
    [recipient],
    [requester_id],
    [submitter_id],
    [assignee_id],
    [organization_id],
    [group_id],
    [forum_topic_id],
    [problem_id],
    [has_incidents],
    [is_public],
    [due_at],
    [custom_status_id],
    [brand_id],
    [allow_channelback],
    [allow_attachments],
    [from_messaging_channel]
FROM OPENJSON(@Json)
WITH (
    [id] INT '$.id',
    [url] NVARCHAR(255) '$.url',
    [external_id] NVARCHAR(255) '$.external_id',
    [created_at] DATETIME2 '$.created_at',
    [updated_at] DATETIME2 '$.updated_at',
    [generated_timestamp] BIGINT '$.generated_timestamp',
    [type] NVARCHAR(50) '$.type',
    [subject] NVARCHAR(255) '$.subject',
    [raw_subject] NVARCHAR(255) '$.raw_subject',
    [description] NVARCHAR(MAX) '$.description',
    [priority] NVARCHAR(50) '$.priority',
    [status] NVARCHAR(50) '$.status',
    [recipient] NVARCHAR(255) '$.recipient',
    [requester_id] BIGINT '$.requester_id',
    [submitter_id] BIGINT '$.submitter_id',
    [assignee_id] BIGINT '$.assignee_id',
    [organization_id] BIGINT '$.organization_id',
    [group_id] BIGINT '$.group_id',
    [forum_topic_id] BIGINT '$.forum_topic_id',
    [problem_id] BIGINT '$.problem_id',
    [has_incidents] BIT '$.has_incidents',
    [is_public] BIT '$.is_public',
    [due_at] DATETIME2 '$.due_at',
    [custom_status_id] BIGINT '$.custom_status_id',
    [brand_id] BIGINT '$.brand_id',
    [allow_channelback] BIT '$.allow_channelback',
    [allow_attachments] BIT '$.allow_attachments',
    [from_messaging_channel] BIT '$.from_messaging_channel'
) AS t;


CREATE TABLE Ticket_Metrics (
	[Agent Wait Time In Minutes Business] int,
    [Agent Wait Time In Minutes Calendar] int,
    [Assigned At] datetime2,
    [Assignee Stations] int,
    [Assignee Updated At] datetime2,
    [First Resolution Time Business] int,
    [First Resolution Time Calendar] int,
    [Full Resolution Time Business] int,
    [Full Resolution Time Calendar] int,
    [Group Stations] int,
    [Initially Assigned At] datetime2,
    [Latest Comment Added At] datetime2,
    [On Hold Time Business] int,
    [On Hold Time Calendar] int,
    [Reopens] int,
    [Replies] int,
    [Reply Time In Minutes Business] int,
    [Reply Time In Minutes Calendar] int,
    [Requester Updated At] datetime2,
    [Requester Wait Time Business] int,
    [Requester Wait Time Calendar] int,
    [Solved At] datetime2,
    [Status Updated At] datetime2,
    [Ticket Id] int,
	[Created At] datetime2,
    [Updated At] datetime2,
    [URL] nvarchar(255)
);

INSERT INTO Ticket_Metrics 
SELECT
	[Agent Wait Time In Minutes Business],
    [Agent Wait Time In Minutes Calendar],
    [Assigned At],
    [Assignee Stations],
    [Assignee Updated At],
    [First Resolution Time Business],
    [First Resolution Time Calendar],
    [Full Resolution Time Business],
    [Full Resolution Time Calendar],
    [Group Stations],
    [Initially Assigned At],
    [Latest Comment Added At],
    [On Hold Time Business],
    [On Hold Time Calendar],
    [Reopens],
    [Replies],
    [Reply Time In Minutes Business],
    [Reply Time In Minutes Calendar],
    [Requester Updated At],
    [Requester Wait Time Business],
    [Requester Wait Time Calendar],
    [Solved At],
    [Status Updated At],
    [Ticket Id],
	[Created At],
    [Updated At],
    [URL]
FROM OPENJSON(@Json) 
WITH (
	[Agent Wait Time In Minutes Business] int '$.metric_set.agent_wait_time_in_minutes.business',
    [Agent Wait Time In Minutes Calendar] int '$.metric_set.agent_wait_time_in_minutes.calendar',
    [Assigned At] datetime2 '$.metric_set.assigned_at',
    [Assignee Stations] int '$.metric_set.assignee_stations',
    [Assignee Updated At] datetime2 '$.metric_set.assignee_updated_at',
    [First Resolution Time Business] int '$.metric_set.first_resolution_time_in_minutes.business',
    [First Resolution Time Calendar] int '$.metric_set.first_resolution_time_in_minutes.calendar',
    [Full Resolution Time Business] int '$.metric_set.full_resolution_time_in_minutes.business',
    [Full Resolution Time Calendar] int '$.metric_set.full_resolution_time_in_minutes.calendar',
    [Group Stations] int '$.metric_set.group_stations',
    [Initially Assigned At] datetime2 '$.metric_set.initially_assigned_at',
    [Latest Comment Added At] datetime2 '$.metric_set.latest_comment_added_at',
    [On Hold Time Business] int '$.metric_set.on_hold_time_in_minutes.business',
    [On Hold Time Calendar] int '$.metric_set.on_hold_time_in_minutes.calendar',
    [Reopens] int '$.metric_set.reopens',
    [Replies] int '$.metric_set.replies',
    [Reply Time In Minutes Business] int '$.metric_set.reply_time_in_minutes.business',
    [Reply Time In Minutes Calendar] int '$.metric_set.reply_time_in_minutes.calendar',
    [Requester Updated At] datetime2 '$.metric_set.requester_updated_at',
    [Requester Wait Time Business] int '$.metric_set.requester_wait_time_in_minutes.business',
    [Requester Wait Time Calendar] int '$.metric_set.requester_wait_time_in_minutes.calendar',
    [Solved At] datetime2 '$.metric_set.solved_at',
    [Status Updated At] datetime2 '$.metric_set.status_updated_at',
    [Ticket Id] int '$.metric_set.ticket_id',
	[Created At] datetime2 '$.metric_set.created_at',
    [Updated At] datetime2 '$.metric_set.updated_at',
    [URL] nvarchar(255) '$.metric_set.url'
) AS m;

-- Create the Tags table
CREATE TABLE Tags (
        [TicketID] NVARCHAR(100),
        [Tag] NVARCHAR(255)
    );

    -- Insert data into Tags table from JSON
    INSERT INTO Tags
    SELECT 
        [id] AS [TicketID],
        [value] AS [Tag]
    FROM OPENJSON(@JSON)
    WITH (
        id NVARCHAR(100),
        tags NVARCHAR(MAX) AS JSON
    )
    CROSS APPLY OPENJSON(tags) 
    WITH (
        value NVARCHAR(255) '$'
    );

-- Create the Via table
CREATE TABLE Via (
	[TicketID] INT,
	[Channel] NVARCHAR(50),
    [Source_Channel] NVARCHAR(50),
    [Source_Subject] NVARCHAR(255),
    [Source_Ticket_Id] INT,
    [Rel] NVARCHAR(50),
    [Source_From_Name] NVARCHAR(255),
    [Source_From_Address] NVARCHAR(255),
    [Source_To_Name] NVARCHAR(255),
    [Source_To_Address] NVARCHAR(255)
);

-- Insert into Via table
INSERT INTO Via
SELECT 
	[id] AS [TicketID],
	[channel],
    [source_channel],
    [source_subject],
    [source_ticket_id],
    [rel],
    [source_from_name],
    [source_from_address],
    [source_to_name],
    [source_to_address]
FROM OPENJSON(@Json)
WITH (
	[id] INT '$.id',
	[channel] NVARCHAR(50) '$.via.channel',                      -- Main channel
    [source_channel] NVARCHAR(50) '$.via.source.from.channel',   -- From -> source channel
    [source_subject] NVARCHAR(255) '$.via.source.from.subject',  -- From -> source subject
    [source_ticket_id] INT '$.via.source.from.ticket_id',        -- From -> source ticket ID
    [rel] NVARCHAR(50) '$.via.source.rel',                       -- From -> relation
    [source_from_name] NVARCHAR(255) '$.via.source.from.name',   -- From -> source name
    [source_from_address] NVARCHAR(255) '$.via.source.from.address', -- From -> source address
    [source_to_name] NVARCHAR(255) '$.via.source.to.name',       -- To -> target name
    [source_to_address] NVARCHAR(255) '$.via.source.to.address'  -- To -> target address
) AS v;

-- Output the number of records processed for the Tickets table
DECLARE @TicketsProcessed INT = @@ROWCOUNT;
PRINT 'Tickets Records Processed: ' + CAST(@TicketsProcessed AS NVARCHAR(10));


-- Create the Users table
CREATE TABLE Users (
    [Id] BIGINT PRIMARY KEY,
    [Email] NVARCHAR(255),
    [Name] NVARCHAR(255),
    [Phone] NVARCHAR(50),
    [Photo_Url] NVARCHAR(255),
    [Role] NVARCHAR(50),
    [Active] BIT,
    [Last_Login_At] DATETIME2
);

-- Insert into the Users table using the Users JSON
INSERT INTO Users
SELECT
    [id],
    [email],
    [name],
    [phone],
    [photo_url] AS Photo_Url,
    [role],
    [active],
    [last_login_at] AS Last_Login_At
FROM OPENJSON(@JSONUsers)
WITH (
    [id] BIGINT '$.id',
    [email] NVARCHAR(255) '$.email',
    [name] NVARCHAR(255) '$.name',
    [phone] NVARCHAR(50) '$.phone',
    [photo_url] NVARCHAR(255) '$.photo.content_url', -- Adjusted for the path
    [role] NVARCHAR(50) '$.role',
    [active] BIT '$.active',
    [last_login_at] DATETIME2 '$.last_login_at'
) AS u;

-- Output the number of records processed for the Users table
DECLARE @UsersProcessed INT = @@ROWCOUNT;
PRINT 'Users Records Processed: ' + CAST(@UsersProcessed AS NVARCHAR(10));


End;