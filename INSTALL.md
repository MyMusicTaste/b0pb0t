# INSTALLATION

*[Disclaimer] We are currently working on an AWS CloudFormation which will allow easy installation for Bopbot. The following is merely a list of installation instructions should you want to do so yourself now, but the working bot can also be previewed at [here](https://slack.com/oauth/authorize?scope=bot,channels:write,im:write,im:history,reminders:write&state=install&client_id=70107175334.85498289508).*

Installation requires setup of six components: Yelp, DynamoDB, APIGateway, Lambda, SNS, and a Slack application. The instructions for each are below, in order.

### Create a Yelp application

Create a Yelp application [here](https://www.yelp.com/developers). You will need the credentials for the next step.

### Setup DynamoDB and authorize your codebase

You will need to create a DynamoDB instance. Once created, you will need the following 6 tables:

    import boto3
    
    db = boto3.resource('dynamodb', region_name=DYNAMO_REGION_NAME, endpoint_url=DYNAMO_ENDPOINT_URL)
    
    db.create_table(table_name='Bot_phrase', key_schema=[{'AttributeName': 'Key', 'KeyType': 'HASH'}, {'AttributeName': 'Phrase', 'KeyType': 'RANGE'}], attribute_definitions = [{'AttributeName': 'Key', 'AttributeType': 'S'}, {'AttributeName': 'Phrase', 'AttributeType': 'S'}], provisioned_throughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5})
    db.create_table(table_name='Channel_poll', key_schema=[{'AttributeName': 'Channel_id', 'KeyType': 'HASH'}], attribute_definitions=[{'AttributeName': 'Channel_id', 'AttributeType': 'S'}], provisioned_throughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5})
    db.create_table(table_name='Restaurant_list', key_schema=[{'AttributeName': 'Location', 'KeyType': 'HASH'}, {'AttributeName': 'Yelp_id', 'KeyType': 'RANGE'}], attribute_definitions = [{'AttributeName': 'Location', 'AttributeType': 'S'}, {'AttributeName': 'Yelp_id', 'AttributeType': 'S'}], provisioned_throughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5})
    db.create_table(table_name='SlackTeamBot', key_schema=[{'AttributeName': 'Team_id', 'KeyType': 'HASH'}, {'AttributeName': 'User_id', 'KeyType': 'RANGE'}], attribute_definitions = [{'AttributeName': 'Team_id', 'AttributeType': 'S'}, {'AttributeName': 'User_id', 'AttributeType': 'S'}], provisioned_throughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}) 
    db.create_table(table_name='User_status', key_schema=[{'AttributeName': 'User_id', 'KeyType': 'HASH'}], attribute_definitions=[{'AttributeName': 'User_id', 'AttributeType': 'S'}], provisioned_throughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5})
    db.create_table(table_name='Vote_table', key_schema=[{'AttributeName': 'Message_ts', 'KeyType': 'HASH'}, {'AttributeName': 'User_id', 'KeyType': 'RANGE'}], attribute_definitions = [{'AttributeName': 'Message_ts', 'AttributeType': 'S'}, {'AttributeName': 'User_id', 'AttributeType': 'S'}], provisioned_throughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5})

You then need to edit ```conf.py``` and add your DynamoDB credentials and Yelp credentials to this file. Placement should be obvious.

Finally, pre-populate two of the tables using functions in the ```debutTest.py``` file.

    from debutTest import set_phrase, set_tutorial_restaurant
    set_phrase()
    set_tutorial_restaurant()

## Create 5 AWS Lambda functions

You will need to create and configure the following 5 Lambda functions:
    
1. ```slack_event_receiver``` (use 5 second timeout, configuration - Handler: event_receiver.lambda_handler)
2. ```slack_event_handler``` (use 5 minute timeout, configuration - Handler: event_handler.lambda_handler)
3. ```slack_im_receiver``` (use 5 second timeout, configuration - Handler: im_receiver.lambda_handler)
4. ```slack_oauth``` (use 1 minute timeout, configuration - Handler: oauth.lambda_handler)
5. ```slack_poll_timer``` (use 3 minute timeout, configuration - Handler: poll_timer.lambda_handler)

### Create AWS APIGateway and add 1 endpoint per Lambda function

You will need to create a new AWS API on APIGateway, with one endpoint per Lambda function with the following configurations:
    
1. ```slack_event_handler``` - method 'ANY'
    * Integration Request - Body Mapping Templates - add two `Content-Type`
        a. `application/json` - template - `{ "body": $input.json("$") }`
        b. `application/x-www-form-urlencoded` - template - `{ "body": $input.json("$") }`
2. `slack_event_receiver` - method 'ANY'
    * Integration Request - Body Mapping Templates - add two `Content-Type`
        a. `application/json` - template - `{ "body": $input.json("$") }`
        b. `application/x-www-form-urlencoded` - template - `{ "body": $input.json("$") }`
    * Method Response
        a. Add response - Http status 400
    * Integration Response - add two responses
        a. Lambda Error Regex: `'.*''` - Method response status: '200'
        b. Lambda Error Regex: `'.*Bad Request.*'` - Method response status: '400'
3. `slack_im_receiver` - method 'ANY'
    * Integration Request - Body Mapping Templates - add two `Content-Type`
        a. `application/json` - template - select 'Method Request passthrough'
        b. `application/x-www-form-urlencoded` - template - select 'Method Request passthrough'
4. `slack_oauth` - method 'ANY'
    * Integration Request - Body Mapping Templates - add one `Content-Type`
        a. `application/json` - template - select 'Method Request passthrough'
    * Method Response
        a. Add response headers for 200 - 'Content-Type'
        b. Add response headers for 400 - 'Content-Type'
    * Integration Response - add two responses
        a. Lambda Error Regex: `'.*''` - Method response status: '200'
            - Header Mappings - `'Content-Type' : 'text/html'`
            - Body Mapping Templates - add `'text/html'` - template - html for status 200
        b. Lambda Error Regex: `'.*Bad Request.*'` - Method response status: '400'			
            - Header Mappings - `'Content-Type' : 'text/html'`
            - Body Mapping Templates - add `'text/html'` - template - html for status 400
5. `slack_poll_timer` - method 'ANY'
    * Integration Request - Body Mapping Templates - add three `Content-Type`
        a. `application/json` - template - `{ "body": $input.json("$") }`
        b. `application/x-www-form-urlencoded` - template - `{ "body": $input.json("$") }`
        c. `application/xml` - template - `{ "body": $input.json("$") }`

### Create a Slack application

You will need to create a Slack application for your bot. Creation/configuration steps below:
    
1. Sign in to Slack
2. Navigate to the [Slack apps portal](https://api.slack.com/apps)
3. Click the ‘Create New App’ button. Add the following configurations in each sub-menu:
    a. Basic Information menu - add your personal basic information
    b. OAuth & Permissions menu - configure the redirect url(s) to point to the endpoint(s) of ```slack_oauth``` Lambda above
    c. Bot Users menu - create a friendly bot user
    d. Interactive Messages menu - configure the request url to point to the endpoint of ```slack_im_receiver``` Lambda above
    e. Event Subscriptions menu - enable events for your app, configure the request url to point to the endpoint of ```slack_event_receiver``` above, and add two bot events: ```message.im``` and ```team_join```
4. You will also need to update your Slack team settings to allow everyone except guests to archive channels. You can find this setting in ```Permissions -> Channel Management```
5. You then need to edit ```conf.py``` and add your Slack client id and secret to this file. Placement should be obvious.

### Setup AWS SNS and connect Lambda to the Slack application

You will need to create 3 SNS topics:
    
1. ```slack_event``` - adds a Lambda subscription to the ```slack_event_handler``` Lambda function above
2. ```slack_IM``` - adds a Lambda subscription to the ```slack_im_receiver``` Lambda function above
3. ```slack_timer``` - adds a Lambda subscription to the ```slack_poll_timer``` Lambda function above

You then need to edit ```conf.py``` and add your SNS topic names. Placement should be obvious.
        
### Bonus: Install a custom emoji for your Bopbot

Like our cute Bopbot emoji?

![Fancy GIFs](img/emoji.gif) 

Add this or your own custom emoji to Slack [here](https://mymusictaste.slack.com/customize/emoji).