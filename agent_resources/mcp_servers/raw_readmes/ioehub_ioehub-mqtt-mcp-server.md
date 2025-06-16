# IoEHub MQTT MCP 서버

## 1. 개요

이 문서는 MQTT를 통해 온도 센서 데이터를 읽고 LED를 제어하는 MCP(Model Context Protocol) 서버를 설명합니다. 이 서버는 FastMCP 프레임워크를 기반으로 하며, JSON-RPC 프로토콜을 사용하여 통신합니다.

### 1.1 구조도

<svg viewBox="0 0 800 600" xmlns="http://www.w3.org/2000/svg">
  <!-- MCP Client Box -->
  <rect x="50" y="100" width="200" height="120" rx="5" ry="5" fill="white" stroke="black" stroke-width="2"/>
  <text x="150" y="140" text-anchor="middle" font-family="Arial" font-size="16" font-weight="bold">MCP Client</text>
  <text x="150" y="165" text-anchor="middle" font-family="Arial" font-size="14">(Claude AI)</text>

  <!-- MCP Server Box -->
  <rect x="550" y="100" width="200" height="120" rx="5" ry="5" fill="white" stroke="black" stroke-width="2"/>
  <text x="650" y="140" text-anchor="middle" font-family="Arial" font-size="16" font-weight="bold">MCP Server</text>
  <text x="650" y="165" text-anchor="middle" font-family="Arial" font-size="14">(Python/FastMCP)</text>

  <!-- Arrow definitions -->
  <defs>
    <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
      <polygon points="0 0, 10 3.5, 0 7" fill="black"/>
    </marker>
  </defs>

  <!-- JSON-RPC Arrow -->
  <line x1="250" y1="135" x2="550" y2="135" stroke="black" stroke-width="2" marker-end="url(#arrowhead)" stroke-dasharray="5,5"/>
  <line x1="550" y1="165" x2="250" y2="165" stroke="black" stroke-width="2" marker-end="url(#arrowhead)"/>
  
  <!-- Labels for JSON-RPC -->
  <text x="400" y="120" text-anchor="middle" font-family="Arial" font-size="14" font-weight="bold">JSON-RPC</text>
  <text x="400" y="140" text-anchor="middle" font-family="Arial" font-size="12">(stdio)</text>
  <text x="400" y="185" text-anchor="middle" font-family="Arial" font-size="12">Request/Response</text>
  
  <!-- MQTT Broker Box -->
  <rect x="300" y="300" width="200" height="120" rx="5" ry="5" fill="white" stroke="black" stroke-width="2"/>
  <text x="400" y="340" text-anchor="middle" font-family="Arial" font-size="16" font-weight="bold">MQTT Broker</text>
  <text x="400" y="365" text-anchor="middle" font-family="Arial" font-size="14">(172.30.1.100)</text>

  <!-- Bidirectional arrows for MQTT connections -->
  <!-- Between Server and Broker -->
  <line x1="650" y1="220" x2="500" y2="280" stroke="black" stroke-width="2"/>
  <line x1="500" y1="280" x2="520" y2="273" stroke="black" stroke-width="2"/>
  <line x1="500" y1="280" x2="507" y2="295" stroke="black" stroke-width="2"/>
  
  <line x1="500" y1="340" x2="650" y2="220" stroke="black" stroke-width="2"/>
  <line x1="650" y1="220" x2="635" y2="230" stroke="black" stroke-width="2"/>
  <line x1="650" y1="220" x2="640" y2="212" stroke="black" stroke-width="2"/>
  
  <!-- MQTT Label for Server-Broker -->
  <text x="550" y="250" text-anchor="middle" font-family="Arial" font-size="14" font-weight="bold">MQTT (JSON)</text>

  <!-- IoT Device Box -->
  <rect x="300" y="500" width="200" height="100" rx="5" ry="5" fill="white" stroke="black" stroke-width="2"/>
  <text x="400" y="535" text-anchor="middle" font-family="Arial" font-size="16" font-weight="bold">IoT Device</text>
  <text x="400" y="560" text-anchor="middle" font-family="Arial" font-size="14">(Temperature/LED)</text>

  <!-- Bidirectional arrows for MQTT connections -->
  <!-- Between Broker and Device -->
  <line x1="385" y1="420" x2="385" y2="500" stroke="black" stroke-width="2"/>
  <line x1="385" y1="500" x2="378" y2="480" stroke="black" stroke-width="2"/>
  <line x1="385" y1="500" x2="392" y2="480" stroke="black" stroke-width="2"/>
  
  <line x1="415" y1="500" x2="415" y2="420" stroke="black" stroke-width="2"/>
  <line x1="415" y1="420" x2="408" y2="440" stroke="black" stroke-width="2"/>
  <line x1="415" y1="420" x2="422" y2="440" stroke="black" stroke-width="2"/>
  
  <!-- MQTT Label for Broker-Device -->
  <text x="470" y="460" text-anchor="middle" font-family="Arial" font-size="14" font-weight="bold">MQTT (JSON)</text>
</svg>

### 1.2 Key Components:

1. MCP Client (Claude AI)

- Provides user interface

- Sends JSON-RPC requests to MCP Server

- Displays results to user

1. MCP Server (Python/FastMCP)

- Processes client requests

- Communicates with MQTT Broker

- Translates between JSON-RPC and MQTT protocols

1. MQTT Broker (172.30.1.100)

- Central hub for MQTT messages

- Routes messages between server and devices

- Handles publish/subscribe message pattern

1. IoT Device (Temperature Sensor/LED)

- Physical hardware devices

- Provides temperature data

- Controls LED states based on commands

### Data Flow:

1. Client → Server: Function call ioehub_mqtt_get_temperature() or ioehub_mqtt_set_led()

2. Server → Broker: Publishes MQTT message (topic: ioehub/mcp/command)

3. Broker → Device: Forwards command to appropriate device

4. Device → Broker: Publishes response with data (topic: ioehub/mcp/response)

5. Broker → Server: Delivers response to subscribed server

6. Server → Client: Returns function call result with processed data

This vertical layout clearly shows the hierarchical flow of communication from client through server and broker to the IoT devices.

## 2. 시스템 구성

- **프레임워크**: FastMCP
- **통신 프로토콜**: MQTT, JSON-RPC 2.0
- **구현 언어**: Python
- **지원 기능**: 온도 측정, LED 제어

## 3. MQTT 설정

```
MQTT_BROKER = "172.30.1.100"
MQTT_PORT = 1883
MQTT_USERNAME = "ioehub"
MQTT_PASSWORD = "password"
MQTT_PUBLISH_TOPIC = "ioehub/mcp/command"
MQTT_SUBSCRIBE_TOPIC = "ioehub/mcp/response"
```

## 4. 구현된 기능

### 4.1 온도 측정 (`ioehub_mqtt_get_temperature`)

- **설명**: MQTT를 통해 온도 센서에서 현재 온도 데이터를 읽어옵니다.
- **반환 값**: 현재 온도(섭씨)를 문자열로 반환
- **기본 핀**: 13번

### 4.2 LED 제어 (`ioehub_mqtt_set_led`)

- **설명**: MQTT를 통해 지정된 핀의 LED 상태를 제어합니다.
- **파라미터**:
  - `pin` (정수): LED 핀 번호 (기본값: 0)
  - `state` (정수): LED 상태 (1=켜짐, 0=꺼짐)
- **반환 값**: 작업 성공 여부(True/False)

## 5. 메시지 형식

### 5.1 온도 측정 요청

```json
{
  "function": "ioehub_mqtt_get_temperature",
  "params": {
    "pin": 13
  }
}
```

### 5.2 온도 측정 응답

```json
{
  "function": "ioehub_mqtt_get_temperature",
  "result": 26.5,
  "timestamp": "749817"
}
```

### 5.3 LED 제어 요청

```json
{
  "function": "ioehub_mqtt_set_led",
  "params": {
    "pin": 0,
    "state": 1
  }
}
```

### 5.4 LED 제어 응답

```json
{
  "function": "ioehub_mqtt_set_led",
  "result": true,
  "timestamp": "749820"
}
```

## 6. 작동 방식

1. **서버 초기화**:

   - MQTT 클라이언트 생성 및 설정
   - 구독 토픽 설정 (ioehub/mcp/response)
   - FastMCP 인스턴스 생성

2. **연결 프로세스**:

   - MQTT 브로커에 연결
   - 백그라운드 스레드에서 메시지 수신 대기

3. **함수 호출 처리**:

   - MCP 도구 호출 시 해당 함수 실행
   - MQTT를 통해 요청 전송
   - 응답 대기 (최대 5초)
   - 결과 반환

4. **메시지 수신 처리**:
   - 구독 토픽에서 메시지 수신
   - JSON 파싱 및 데이터 추출
   - 응답 플래그 설정

## 7. 오류 처리

- **응답 타임아웃**: 5초 이내에 응답이 없으면 기본값 반환
- **JSON 파싱 오류**: 잘못된 형식의 메시지 처리
- **MQTT 연결 오류**: 연결 실패 시 오류 메시지 출력

## 8. 사용 방법

### 8.1 서버 실행

```bash
python mcp_server.py
```

### 8.2 클라이언트에서 함수 호출

```python
# MCP 클라이언트 예시
temperature = client.invoke("ioehub_mqtt_get_temperature")
print(f"현재 온도: {temperature}°C")

# LED 켜기
result = client.invoke("ioehub_mqtt_set_led", {"pin": 0, "state": 1})
print(f"LED 켜기 결과: {'성공' if result else '실패'}")
```

## 9. mcp server 설정 (windows claude desktop)

```
{
  "mcpServers": {
    "IoEHubMqttMcpServer": {
        "command":
           "Your project path\\.venv\\Scripts\\python.exe",

        "args": [
	        "Your project path\\mcp_server.py"
	        ]

    }
  }
}
```

## 10. python 환경 구축(windows)

```
cd "your project path"
uv venv .venv
uv pip install mcp
uv pip install paho-mqtt
```

## 11. 제한 사항 및 참고사항

- MQTT 브로커가 실행 중이어야 합니다.
- 응답 처리 시 'function' 필드를 확인하여 적절한 응답을 식별합니다.
- 모든 디버그 메시지는 stdout이 아닌 stderr로 출력되어야 합니다.
- 실제 하드웨어와 통신하기 위해서는 해당 장치에서 MQTT 클라이언트가 실행되어야 합니다.
