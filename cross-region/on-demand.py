import boto3
import time
import json
from datetime import datetime, timedelta

cw_region = "Agent가 위치한 region"
eval_region = "Evaluation 수행할 region"
agent_id = "AgentCore Runtime ID"
session_id = "Session ID"
lookback_window_min = 1440 # 지난 24시간 조회

def query_logs(log_group_name, query_string):
    client = boto3.client('logs', region_name=cw_region)
    start_time = datetime.now() - timedelta(minutes=lookback_window_min) 
    end_time = datetime.now()

    query_id = client.start_query(
        logGroupName=log_group_name,
        startTime=int(start_time.timestamp()),
        endTime=int(end_time.timestamp()),
        queryString=query_string
    )['queryId']

    while (result := client.get_query_results(queryId=query_id))['status'] not in ['Complete', 'Failed']:
        time.sleep(1)

    if result['status'] == 'Failed':
        raise Exception("Query failed")
    return result['results']

def query_session_logs(log_group_name, session_id, **kwargs):
    query = f"""fields @timestamp, @message
    | filter ispresent(scope.name) and ispresent(attributes.session.id)
    | filter attributes.session.id = "{session_id}"
    | sort @timestamp asc"""
    return query_logs(log_group_name, query, **kwargs)

def query_agent_runtime_logs(agent_id, endpoint, session_id, **kwargs):
    return query_session_logs(
        f"/aws/bedrock-agentcore/runtimes/{agent_id}-{endpoint}",
        session_id, **kwargs)

def query_aws_spans_logs(session_id, **kwargs):
    return query_session_logs("aws/spans", session_id, **kwargs)

def extract_messages_as_json(query_results):
    return [json.loads(f['value']) for row in query_results
            for f in row if f['field'] == '@message'
            and f['value'].strip().startswith('{')]

def get_session_span_logs():
    agent_runtime_logs = query_agent_runtime_logs(
        agent_id=agent_id, endpoint="DEFAULT", session_id=session_id
    )
    print(f"Downloaded {len(agent_runtime_logs)} runtime-log entries")

    aws_span_logs = query_aws_spans_logs(session_id=session_id)
    print(f"Downloaded {len(aws_span_logs)} aws/span entries")

    session_span_logs = extract_messages_as_json(aws_span_logs) + extract_messages_as_json(agent_runtime_logs)
    print(f"Returning {len(aws_span_logs) + len(agent_runtime_logs)} total records")
    return session_span_logs

# Cloudwatch에서 span 조회
session_span_logs = get_session_span_logs()

# 필요 시 재사용을 위해 JSON으로 저장
session_span_logs_file_name = "ace-demo-session.json"
with open(session_span_logs_file_name, "w") as f:
    json.dump(session_span_logs, f, indent=2)

# JSON 파일 읽기
# with open(session_span_logs_file_name, "r") as f:
#     session_span_logs = json.load(f)

# AgentCore client 초기화
ace_dp_client = boto3.client('bedrock-agentcore', region_name = eval_region)

# 평가 수행
response = ace_dp_client.evaluate(
    evaluatorId = "Builtin.ToolSelectionAccuracy", # Evaluator ID
    evaluationInput = {"sessionSpans": session_span_logs})

print(response["evaluationResults"])