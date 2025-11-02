# Admin Push Notifications Guide

Complete guide for implementing Firebase Cloud Messaging (FCM) push notifications for admin mobile applications.

---

## Table of Contents

1. [Overview](#overview)
2. [Firebase Setup](#firebase-setup)
3. [Android Implementation](#android-implementation)
4. [iOS Implementation](#ios-implementation)
5. [Flutter Implementation](#flutter-implementation)
6. [React Native Implementation](#react-native-implementation)
7. [Backend Integration](#backend-integration)
8. [Testing](#testing)
9. [Troubleshooting](#troubleshooting)

---

## Overview

### What is Admin Push Notification?

When a new device registers in the system, all logged-in admin devices receive an instant push notification.

### Notification Flow

```
New Device Registers
        ?
Backend Server
        ?
Firebase Cloud Messaging (FCM)
        ?
Admin Mobile Devices
        ?
Push Notification Displayed
```

### Notification Types

**Device Registration Notification:**
```
Title: "?? New Device Registered"
Body: "Samsung Galaxy S21 (SexyChat)"
Data: {
  "type": "device_registered",
  "device_id": "abc123",
  "model": "Samsung Galaxy S21",
  "app_type": "sexychat"
}
```

---

## Firebase Setup

### Step 1: Create Firebase Project

See [Firebase Setup Guide](./FIREBASE.md#admin-firebase-setup) for creating the admin Firebase project.

### Step 2: Download Configuration Files

**For Android:**
1. Go to Firebase Console ? Project Settings
2. Click on your Android app
3. Download `google-services.json`
4. Place in `android/app/` directory

**For iOS:**
1. Go to Firebase Console ? Project Settings
2. Click on your iOS app
3. Download `GoogleService-Info.plist`
4. Add to Xcode project

---

## Android Implementation

### Step 1: Add Dependencies

**File:** `android/app/build.gradle`

```gradle
plugins {
    id 'com.android.application'
    id 'com.google.gms.google-services'  // Add this
}

dependencies {
    // Firebase BoM (Bill of Materials)
    implementation platform('com.google.firebase:firebase-bom:32.7.0')
    
    // Firebase Cloud Messaging
    implementation 'com.google.firebase:firebase-messaging'
    
    // Optional: Analytics
    implementation 'com.google.firebase:firebase-analytics'
}
```

**File:** `android/build.gradle`

```gradle
buildscript {
    dependencies {
        classpath 'com.google.gms:google-services:4.4.0'  // Add this
    }
}
```

### Step 2: Add Permissions

**File:** `android/app/src/main/AndroidManifest.xml`

```xml
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    
    <!-- Permissions -->
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />
    
    <application>
        <!-- Firebase Messaging Service -->
        <service
            android:name=".MyFirebaseMessagingService"
            android:exported="false">
            <intent-filter>
                <action android:name="com.google.firebase.MESSAGING_EVENT" />
            </intent-filter>
        </service>
        
        <!-- Default notification channel -->
        <meta-data
            android:name="com.google.firebase.messaging.default_notification_channel_id"
            android:value="admin_notifications" />
    </application>
</manifest>
```

### Step 3: Create Firebase Messaging Service

**File:** `MyFirebaseMessagingService.java`

```java
package com.example.adminapp;

import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.os.Build;
import android.util.Log;

import androidx.core.app.NotificationCompat;

import com.google.firebase.messaging.FirebaseMessagingService;
import com.google.firebase.messaging.RemoteMessage;

import org.json.JSONObject;

public class MyFirebaseMessagingService extends FirebaseMessagingService {
    
    private static final String TAG = "FCMService";
    private static final String CHANNEL_ID = "admin_notifications";
    
    @Override
    public void onNewToken(String token) {
        super.onNewToken(token);
        Log.d(TAG, "New FCM Token: " + token);
        
        // Save token locally
        saveTokenToPreferences(token);
        
        // Send to backend (if user is logged in)
        sendTokenToBackend(token);
    }
    
    @Override
    public void onMessageReceived(RemoteMessage remoteMessage) {
        super.onMessageReceived(remoteMessage);
        
        Log.d(TAG, "Message received from: " + remoteMessage.getFrom());
        
        // Check if message contains data payload
        if (remoteMessage.getData().size() > 0) {
            Log.d(TAG, "Message data: " + remoteMessage.getData());
            handleDataMessage(remoteMessage.getData());
        }
        
        // Check if message contains notification payload
        if (remoteMessage.getNotification() != null) {
            String title = remoteMessage.getNotification().getTitle();
            String body = remoteMessage.getNotification().getBody();
            Log.d(TAG, "Notification: " + title + " - " + body);
            
            showNotification(title, body, remoteMessage.getData());
        }
    }
    
    private void handleDataMessage(Map<String, String> data) {
        String type = data.get("type");
        
        if ("device_registered".equals(type)) {
            String deviceId = data.get("device_id");
            String model = data.get("model");
            String appType = data.get("app_type");
            
            Log.d(TAG, "New device registered: " + model + " (" + appType + ")");
            
            // Show notification
            showNotification(
                "?? New Device Registered",
                model + " (" + appType + ")",
                data
            );
        }
    }
    
    private void showNotification(String title, String body, Map<String, String> data) {
        // Create notification channel (Android 8.0+)
        createNotificationChannel();
        
        // Intent to open app when notification clicked
        Intent intent = new Intent(this, MainActivity.class);
        intent.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP);
        
        // Add data to intent
        if (data != null) {
            for (Map.Entry<String, String> entry : data.entrySet()) {
                intent.putExtra(entry.getKey(), entry.getValue());
            }
        }
        
        PendingIntent pendingIntent = PendingIntent.getActivity(
            this,
            0,
            intent,
            PendingIntent.FLAG_ONE_SHOT | PendingIntent.FLAG_IMMUTABLE
        );
        
        // Build notification
        NotificationCompat.Builder builder = new NotificationCompat.Builder(this, CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_notification)
            .setContentTitle(title)
            .setContentText(body)
            .setAutoCancel(true)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setContentIntent(pendingIntent)
            .setStyle(new NotificationCompat.BigTextStyle().bigText(body));
        
        // Show notification
        NotificationManager notificationManager = 
            (NotificationManager) getSystemService(Context.NOTIFICATION_SERVICE);
        notificationManager.notify(0, builder.build());
    }
    
    private void createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            CharSequence name = "Admin Notifications";
            String description = "Notifications for admin activities";
            int importance = NotificationManager.IMPORTANCE_HIGH;
            
            NotificationChannel channel = new NotificationChannel(CHANNEL_ID, name, importance);
            channel.setDescription(description);
            channel.enableLights(true);
            channel.enableVibration(true);
            
            NotificationManager notificationManager = getSystemService(NotificationManager.class);
            notificationManager.createNotificationChannel(channel);
        }
    }
    
    private void saveTokenToPreferences(String token) {
        getSharedPreferences("FCM", MODE_PRIVATE)
            .edit()
            .putString("token", token)
            .apply();
    }
    
    private void sendTokenToBackend(String token) {
        // Check if user is logged in
        String accessToken = getSharedPreferences("Auth", MODE_PRIVATE)
            .getString("access_token", null);
        
        if (accessToken != null) {
            // Send to backend (implement your API call here)
            // This will be done during login
        }
    }
}
```

### Step 4: Get FCM Token and Send to Backend

**File:** `MainActivity.java` or your login activity

```java
package com.example.adminapp;

import android.os.Bundle;
import android.util.Log;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

import com.google.android.gms.tasks.OnCompleteListener;
import com.google.android.gms.tasks.Task;
import com.google.firebase.messaging.FirebaseMessaging;

import org.json.JSONObject;

import java.io.IOException;

import okhttp3.Call;
import okhttp3.Callback;
import okhttp3.MediaType;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

public class MainActivity extends AppCompatActivity {
    
    private static final String TAG = "MainActivity";
    private static final String API_BASE_URL = "http://your-server.com";
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        
        // Request notification permission (Android 13+)
        requestNotificationPermission();
        
        // Get FCM token
        getFCMToken();
    }
    
    private void requestNotificationPermission() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(this, 
                    Manifest.permission.POST_NOTIFICATIONS) != 
                    PackageManager.PERMISSION_GRANTED) {
                ActivityCompat.requestPermissions(this,
                    new String[]{Manifest.permission.POST_NOTIFICATIONS}, 101);
            }
        }
    }
    
    private void getFCMToken() {
        FirebaseMessaging.getInstance().getToken()
            .addOnCompleteListener(new OnCompleteListener<String>() {
                @Override
                public void onComplete(Task<String> task) {
                    if (!task.isSuccessful()) {
                        Log.w(TAG, "Fetching FCM token failed", task.getException());
                        return;
                    }
                    
                    // Get new FCM token
                    String fcmToken = task.getResult();
                    Log.d(TAG, "FCM Token: " + fcmToken);
                    
                    // Save locally
                    saveFCMToken(fcmToken);
                    
                    // Will be sent during login
                }
            });
    }
    
    private void saveFCMToken(String token) {
        getSharedPreferences("FCM", MODE_PRIVATE)
            .edit()
            .putString("token", token)
            .apply();
    }
    
    // Call this during login (Step 2 of 2FA)
    public void verify2FA(String username, String otpCode, String tempToken) {
        String fcmToken = getSharedPreferences("FCM", MODE_PRIVATE)
            .getString("token", null);
        
        JSONObject json = new JSONObject();
        try {
            json.put("username", username);
            json.put("otp_code", otpCode);
            json.put("temp_token", tempToken);
            json.put("fcm_token", fcmToken);  // ? Send FCM token
            
            OkHttpClient client = new OkHttpClient();
            RequestBody body = RequestBody.create(
                json.toString(),
                MediaType.parse("application/json")
            );
            
            Request request = new Request.Builder()
                .url(API_BASE_URL + "/auth/verify-2fa")
                .post(body)
                .build();
            
            client.newCall(request).enqueue(new Callback() {
                @Override
                public void onFailure(Call call, IOException e) {
                    Log.e(TAG, "Login failed", e);
                }
                
                @Override
                public void onResponse(Call call, Response response) throws IOException {
                    if (response.isSuccessful()) {
                        String responseData = response.body().string();
                        Log.d(TAG, "Login successful: " + responseData);
                        
                        // Parse response and save access token
                        JSONObject json = new JSONObject(responseData);
                        String accessToken = json.getString("access_token");
                        
                        // Save access token
                        getSharedPreferences("Auth", MODE_PRIVATE)
                            .edit()
                            .putString("access_token", accessToken)
                            .apply();
                        
                        runOnUiThread(() -> {
                            Toast.makeText(MainActivity.this, 
                                "Login successful!", Toast.LENGTH_SHORT).show();
                        });
                    }
                }
            });
            
        } catch (Exception e) {
            Log.e(TAG, "Error", e);
        }
    }
}
```

### Step 5: Handle Notification Click

**File:** `MainActivity.java`

```java
@Override
protected void onCreate(Bundle savedInstanceState) {
    super.onCreate(savedInstanceState);
    setContentView(R.layout.activity_main);
    
    // Handle notification click
    handleNotificationIntent(getIntent());
}

@Override
protected void onNewIntent(Intent intent) {
    super.onNewIntent(intent);
    handleNotificationIntent(intent);
}

private void handleNotificationIntent(Intent intent) {
    if (intent.getExtras() != null) {
        String type = intent.getStringExtra("type");
        
        if ("device_registered".equals(type)) {
            String deviceId = intent.getStringExtra("device_id");
            String model = intent.getStringExtra("model");
            String appType = intent.getStringExtra("app_type");
            
            Log.d(TAG, "Opened from notification: " + deviceId);
            
            // Navigate to device details screen
            Intent deviceIntent = new Intent(this, DeviceDetailsActivity.class);
            deviceIntent.putExtra("device_id", deviceId);
            startActivity(deviceIntent);
        }
    }
}
```

---

## iOS Implementation

### Step 1: Add Firebase SDK

**File:** `Podfile`

```ruby
platform :ios, '13.0'

target 'AdminApp' do
  use_frameworks!
  
  # Firebase
  pod 'Firebase/Core'
  pod 'Firebase/Messaging'
end
```

Run:
```bash
cd ios
pod install
```

### Step 2: Configure Firebase

**File:** `AppDelegate.swift`

```swift
import UIKit
import Firebase
import UserNotifications

@main
class AppDelegate: UIResponder, UIApplicationDelegate, UNUserNotificationCenterDelegate, MessagingDelegate {
    
    func application(_ application: UIApplication,
                     didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {
        
        // Configure Firebase
        FirebaseApp.configure()
        
        // Set messaging delegate
        Messaging.messaging().delegate = self
        
        // Request notification permission
        UNUserNotificationCenter.current().delegate = self
        
        let authOptions: UNAuthorizationOptions = [.alert, .badge, .sound]
        UNUserNotificationCenter.current().requestAuthorization(
            options: authOptions) { granted, _ in
            print("Notification permission granted: \(granted)")
        }
        
        application.registerForRemoteNotifications()
        
        return true
    }
    
    // MARK: - FCM Token
    
    func messaging(_ messaging: Messaging, didReceiveRegistrationToken fcmToken: String?) {
        print("FCM Token: \(fcmToken ?? "")")
        
        // Save token
        if let token = fcmToken {
            UserDefaults.standard.set(token, forKey: "fcm_token")
            
            // Send to backend (if logged in)
            sendTokenToBackend(token)
        }
    }
    
    // MARK: - Remote Notifications
    
    func application(_ application: UIApplication,
                     didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data) {
        Messaging.messaging().apnsToken = deviceToken
    }
    
    func application(_ application: UIApplication,
                     didFailToRegisterForRemoteNotificationsWithError error: Error) {
        print("Failed to register for remote notifications: \(error)")
    }
    
    // MARK: - Notification Handling
    
    // When app is in foreground
    func userNotificationCenter(_ center: UNUserNotificationCenter,
                               willPresent notification: UNNotification,
                               withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void) {
        let userInfo = notification.request.content.userInfo
        print("Notification received in foreground: \(userInfo)")
        
        // Show notification even when app is in foreground
        completionHandler([[.banner, .sound, .badge]])
    }
    
    // When user taps on notification
    func userNotificationCenter(_ center: UNUserNotificationCenter,
                               didReceive response: UNNotificationResponse,
                               withCompletionHandler completionHandler: @escaping () -> Void) {
        let userInfo = response.notification.request.content.userInfo
        print("Notification tapped: \(userInfo)")
        
        handleNotificationTap(userInfo: userInfo)
        completionHandler()
    }
    
    // MARK: - Helper Methods
    
    private func sendTokenToBackend(_ token: String) {
        // Check if user is logged in
        guard let accessToken = UserDefaults.standard.string(forKey: "access_token") else {
            return
        }
        
        // Token will be sent during login
    }
    
    private func handleNotificationTap(userInfo: [AnyHashable: Any]) {
        if let type = userInfo["type"] as? String,
           type == "device_registered" {
            let deviceId = userInfo["device_id"] as? String ?? ""
            let model = userInfo["model"] as? String ?? ""
            
            print("Navigate to device: \(deviceId)")
            
            // Post notification to navigate
            NotificationCenter.default.post(
                name: NSNotification.Name("NavigateToDevice"),
                object: nil,
                userInfo: ["device_id": deviceId]
            )
        }
    }
}
```

### Step 3: Send FCM Token During Login

**File:** `LoginViewController.swift`

```swift
import UIKit

class LoginViewController: UIViewController {
    
    let apiBaseURL = "http://your-server.com"
    
    func verify2FA(username: String, otpCode: String, tempToken: String) {
        // Get FCM token
        let fcmToken = UserDefaults.standard.string(forKey: "fcm_token")
        
        // Prepare request
        let url = URL(string: "\(apiBaseURL)/auth/verify-2fa")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let body: [String: Any] = [
            "username": username,
            "otp_code": otpCode,
            "temp_token": tempToken,
            "fcm_token": fcmToken ?? ""  // ? Send FCM token
        ]
        
        request.httpBody = try? JSONSerialization.data(withJSONObject: body)
        
        // Send request
        URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                print("Error: \(error)")
                return
            }
            
            guard let data = data else { return }
            
            do {
                let json = try JSONSerialization.jsonObject(with: data) as? [String: Any]
                let accessToken = json?["access_token"] as? String
                
                // Save access token
                UserDefaults.standard.set(accessToken, forKey: "access_token")
                
                DispatchQueue.main.async {
                    print("Login successful!")
                    // Navigate to main screen
                }
            } catch {
                print("Parse error: \(error)")
            }
        }.resume()
    }
}
```

### Step 4: Handle Background Notifications

**Enable Background Modes:**
1. Open Xcode
2. Select your target
3. Go to "Signing & Capabilities"
4. Click "+ Capability"
5. Add "Background Modes"
6. Check "Remote notifications"

---

## Flutter Implementation

### Step 1: Add Dependencies

**File:** `pubspec.yaml`

```yaml
dependencies:
  flutter:
    sdk: flutter
  
  firebase_core: ^2.24.2
  firebase_messaging: ^14.7.9
  flutter_local_notifications: ^16.3.0
```

Run:
```bash
flutter pub get
```

### Step 2: Initialize Firebase

**File:** `main.dart`

```dart
import 'package:flutter/material.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';

// Background message handler
Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  await Firebase.initializeApp();
  print('Background message: ${message.messageId}');
}

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Initialize Firebase
  await Firebase.initializeApp();
  
  // Set background message handler
  FirebaseMessaging.onBackgroundMessage(_firebaseMessagingBackgroundHandler);
  
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Admin App',
      home: HomePage(),
    );
  }
}
```

### Step 3: Setup FCM and Local Notifications

**File:** `fcm_service.dart`

```dart
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;

class FCMService {
  static final FCMService _instance = FCMService._internal();
  factory FCMService() => _instance;
  FCMService._internal();
  
  final FirebaseMessaging _fcm = FirebaseMessaging.instance;
  final FlutterLocalNotificationsPlugin _localNotifications = 
      FlutterLocalNotificationsPlugin();
  
  String? _fcmToken;
  
  Future<void> initialize() async {
    // Request permission
    NotificationSettings settings = await _fcm.requestPermission(
      alert: true,
      badge: true,
      sound: true,
    );
    
    if (settings.authorizationStatus == AuthorizationStatus.authorized) {
      print('User granted permission');
    }
    
    // Initialize local notifications
    const AndroidInitializationSettings androidSettings =
        AndroidInitializationSettings('@mipmap/ic_launcher');
    
    const DarwinInitializationSettings iosSettings =
        DarwinInitializationSettings();
    
    const InitializationSettings initSettings = InitializationSettings(
      android: androidSettings,
      iOS: iosSettings,
    );
    
    await _localNotifications.initialize(
      initSettings,
      onDidReceiveNotificationResponse: _onNotificationTapped,
    );
    
    // Create notification channel (Android)
    const AndroidNotificationChannel channel = AndroidNotificationChannel(
      'admin_notifications',
      'Admin Notifications',
      description: 'Notifications for admin activities',
      importance: Importance.high,
    );
    
    await _localNotifications
        .resolvePlatformSpecificImplementation<
            AndroidFlutterLocalNotificationsPlugin>()
        ?.createNotificationChannel(channel);
    
    // Get FCM token
    _fcmToken = await _fcm.getToken();
    print('FCM Token: $_fcmToken');
    
    // Save token
    if (_fcmToken != null) {
      await _saveToken(_fcmToken!);
    }
    
    // Listen for token refresh
    _fcm.onTokenRefresh.listen((token) {
      _fcmToken = token;
      _saveToken(token);
    });
    
    // Handle foreground messages
    FirebaseMessaging.onMessage.listen(_handleForegroundMessage);
    
    // Handle notification taps
    FirebaseMessaging.onMessageOpenedApp.listen(_handleNotificationTap);
    
    // Check if app was opened from notification
    RemoteMessage? initialMessage = await _fcm.getInitialMessage();
    if (initialMessage != null) {
      _handleNotificationTap(initialMessage);
    }
  }
  
  Future<void> _saveToken(String token) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('fcm_token', token);
  }
  
  Future<String?> getToken() async {
    if (_fcmToken != null) return _fcmToken;
    
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('fcm_token');
  }
  
  void _handleForegroundMessage(RemoteMessage message) {
    print('Foreground message: ${message.messageId}');
    
    RemoteNotification? notification = message.notification;
    AndroidNotification? android = message.notification?.android;
    
    if (notification != null && android != null) {
      _localNotifications.show(
        notification.hashCode,
        notification.title,
        notification.body,
        NotificationDetails(
          android: AndroidNotificationDetails(
            'admin_notifications',
            'Admin Notifications',
            channelDescription: 'Notifications for admin activities',
            importance: Importance.high,
            priority: Priority.high,
            icon: '@mipmap/ic_launcher',
          ),
          iOS: DarwinNotificationDetails(),
        ),
        payload: jsonEncode(message.data),
      );
    }
  }
  
  void _handleNotificationTap(RemoteMessage message) {
    print('Notification tapped: ${message.data}');
    
    String? type = message.data['type'];
    
    if (type == 'device_registered') {
      String deviceId = message.data['device_id'] ?? '';
      String model = message.data['model'] ?? '';
      
      print('Navigate to device: $deviceId');
      
      // Navigate to device details
      // You can use Navigator or your routing solution here
    }
  }
  
  void _onNotificationTapped(NotificationResponse response) {
    if (response.payload != null) {
      Map<String, dynamic> data = jsonDecode(response.payload!);
      
      if (data['type'] == 'device_registered') {
        String deviceId = data['device_id'] ?? '';
        print('Navigate to device: $deviceId');
        // Navigate to device details
      }
    }
  }
}
```

### Step 4: Send Token During Login

**File:** `auth_service.dart`

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'fcm_service.dart';

class AuthService {
  static const String apiBaseURL = 'http://your-server.com';
  
  Future<bool> verify2FA({
    required String username,
    required String otpCode,
    required String tempToken,
  }) async {
    try {
      // Get FCM token
      String? fcmToken = await FCMService().getToken();
      
      // Prepare request
      final response = await http.post(
        Uri.parse('$apiBaseURL/auth/verify-2fa'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'username': username,
          'otp_code': otpCode,
          'temp_token': tempToken,
          'fcm_token': fcmToken,  // ? Send FCM token
        }),
      );
      
      if (response.statusCode == 200) {
        Map<String, dynamic> data = jsonDecode(response.body);
        String accessToken = data['access_token'];
        
        // Save access token
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString('access_token', accessToken);
        
        print('Login successful!');
        return true;
      } else {
        print('Login failed: ${response.body}');
        return false;
      }
    } catch (e) {
      print('Error: $e');
      return false;
    }
  }
}
```

### Step 5: Initialize in App

**File:** `main.dart` (update)

```dart
class HomePage extends StatefulWidget {
  @override
  _HomePageState createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  @override
  void initState() {
    super.initState();
    _initializeFCM();
  }
  
  Future<void> _initializeFCM() async {
    await FCMService().initialize();
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Admin App')),
      body: Center(child: Text('Welcome!')),
    );
  }
}
```

---

## React Native Implementation

### Step 1: Install Dependencies

```bash
npm install @react-native-firebase/app @react-native-firebase/messaging
# or
yarn add @react-native-firebase/app @react-native-firebase/messaging
```

### Step 2: Configure Firebase

**For Android:** Place `google-services.json` in `android/app/`

**For iOS:** 
```bash
cd ios && pod install
```
Place `GoogleService-Info.plist` in Xcode project

### Step 3: Setup FCM Service

**File:** `FCMService.js`

```javascript
import messaging from '@react-native-firebase/messaging';
import AsyncStorage from '@react-native-async-storage/async-storage';
import PushNotification from 'react-native-push-notification';

class FCMService {
  async initialize() {
    // Request permission
    const authStatus = await messaging().requestPermission();
    const enabled =
      authStatus === messaging.AuthorizationStatus.AUTHORIZED ||
      authStatus === messaging.AuthorizationStatus.PROVISIONAL;

    if (enabled) {
      console.log('Authorization status:', authStatus);
    }

    // Create notification channel (Android)
    PushNotification.createChannel({
      channelId: 'admin_notifications',
      channelName: 'Admin Notifications',
      channelDescription: 'Notifications for admin activities',
      importance: 4,
      vibrate: true,
    });

    // Get FCM token
    const fcmToken = await messaging().getToken();
    console.log('FCM Token:', fcmToken);
    await AsyncStorage.setItem('fcm_token', fcmToken);

    // Listen for token refresh
    messaging().onTokenRefresh(async (token) => {
      console.log('FCM Token refreshed:', token);
      await AsyncStorage.setItem('fcm_token', token);
    });

    // Handle foreground messages
    messaging().onMessage(async (remoteMessage) => {
      console.log('Foreground message:', remoteMessage);
      this.showLocalNotification(remoteMessage);
    });

    // Handle background/quit messages
    messaging().setBackgroundMessageHandler(async (remoteMessage) => {
      console.log('Background message:', remoteMessage);
    });

    // Handle notification opened app
    messaging().onNotificationOpenedApp((remoteMessage) => {
      console.log('Notification opened app:', remoteMessage);
      this.handleNotificationTap(remoteMessage);
    });

    // Check if app was opened from notification
    const initialNotification = await messaging().getInitialNotification();
    if (initialNotification) {
      this.handleNotificationTap(initialNotification);
    }
  }

  showLocalNotification(remoteMessage) {
    const { notification, data } = remoteMessage;

    PushNotification.localNotification({
      channelId: 'admin_notifications',
      title: notification?.title || 'New Notification',
      message: notification?.body || '',
      userInfo: data,
    });
  }

  handleNotificationTap(remoteMessage) {
    const { data } = remoteMessage;

    if (data.type === 'device_registered') {
      const deviceId = data.device_id;
      console.log('Navigate to device:', deviceId);
      // Navigate to device details screen
    }
  }

  async getToken() {
    return await AsyncStorage.getItem('fcm_token');
  }
}

export default new FCMService();
```

### Step 4: Initialize in App

**File:** `App.js`

```javascript
import React, { useEffect } from 'react';
import { SafeAreaView, Text } from 'react-native';
import FCMService from './FCMService';

function App() {
  useEffect(() => {
    FCMService.initialize();
  }, []);

  return (
    <SafeAreaView>
      <Text>Admin App</Text>
    </SafeAreaView>
  );
}

export default App;
```

### Step 5: Send Token During Login

**File:** `AuthService.js`

```javascript
import FCMService from './FCMService';
import AsyncStorage from '@react-native-async-storage/async-storage';

const API_BASE_URL = 'http://your-server.com';

export async function verify2FA(username, otpCode, tempToken) {
  try {
    // Get FCM token
    const fcmToken = await FCMService.getToken();

    // Send request
    const response = await fetch(`${API_BASE_URL}/auth/verify-2fa`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username,
        otp_code: otpCode,
        temp_token: tempToken,
        fcm_token: fcmToken,  // ? Send FCM token
      }),
    });

    const data = await response.json();

    if (response.ok) {
      const accessToken = data.access_token;
      await AsyncStorage.setItem('access_token', accessToken);
      console.log('Login successful!');
      return true;
    } else {
      console.log('Login failed:', data);
      return false;
    }
  } catch (error) {
    console.error('Error:', error);
    return false;
  }
}
```

---

## Backend Integration

### How Backend Sends Notifications

**File:** `app/services/firebase_admin_service.py`

```python
async def send_device_registration_notification(
    self,
    admin_username: str,
    device_id: str,
    model: str,
    app_type: str
):
    """
    Send push notification to admin when new device registers
    """
    # Get admin's FCM tokens
    admin = await mongodb.db.admins.find_one({"username": admin_username})
    
    if not admin or not admin.get("fcm_tokens"):
        logger.warning(f"No FCM tokens for admin: {admin_username}")
        return
    
    fcm_tokens = admin["fcm_tokens"]
    
    # Prepare notification
    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title="?? New Device Registered",
            body=f"{model} ({app_type})"
        ),
        data={
            "type": "device_registered",
            "device_id": device_id,
            "model": model,
            "app_type": app_type
        },
        tokens=fcm_tokens
    )
    
    # Send notification
    try:
        response = messaging.send_multicast(message, app=self.app)
        logger.info(f"?? Push notification sent to {admin_username}: "
                   f"{response.success_count} success, {response.failure_count} failed")
        
        # Remove invalid tokens
        if response.failure_count > 0:
            failed_tokens = [
                fcm_tokens[idx] 
                for idx, resp in enumerate(response.responses) 
                if not resp.success
            ]
            await self._remove_invalid_tokens(admin_username, failed_tokens)
            
    except Exception as e:
        logger.error(f"? Failed to send notification: {e}")
```

### When Notification is Sent

**File:** `app/main.py` (in `/register` endpoint)

```python
@app.post("/register")
async def register_device(device_data: dict):
    # ... device registration logic ...
    
    # ?? Send push notification to admin
    await firebase_admin_service.send_device_registration_notification(
        admin_username=admin_username,
        device_id=device_id,
        model=model,
        app_type=app_type
    )
    
    logger.info(f"?? Push notification sent to {admin_username}")
```

---

## Testing

### Test Notification from Firebase Console

1. Go to Firebase Console
2. Navigate to **Cloud Messaging**
3. Click **"Send test message"**
4. Enter your FCM token
5. Set notification:
   - **Title:** `Test Notification`
   - **Body:** `This is a test`
6. Click **"Test"**

### Test from Backend

```python
# Test script
import asyncio
from app.services.firebase_admin_service import firebase_admin_service

async def test_notification():
    await firebase_admin_service.send_device_registration_notification(
        admin_username="your_admin",
        device_id="test123",
        model="Test Device",
        app_type="sexychat"
    )

asyncio.run(test_notification())
```

### Verify Token Received by Backend

Check MongoDB:
```javascript
db.admins.findOne({username: "admin"}, {fcm_tokens: 1})
// Should show: { fcm_tokens: ["fcm_token_here", ...] }
```

---

## Troubleshooting

### Android: Notification Not Received

**1. Check Permission:**
```java
if (ContextCompat.checkSelfPermission(this, 
        Manifest.permission.POST_NOTIFICATIONS) != 
        PackageManager.PERMISSION_GRANTED) {
    // Request permission
}
```

**2. Check google-services.json:**
- Ensure file is in `android/app/`
- Package name matches your app

**3. Check FCM Token:**
```java
FirebaseMessaging.getInstance().getToken()
    .addOnCompleteListener(task -> {
        if (task.isSuccessful()) {
            String token = task.getResult();
            Log.d("FCM", "Token: " + token);
        }
    });
```

### iOS: Notification Not Received

**1. Check Capabilities:**
- Push Notifications enabled
- Background Modes ? Remote notifications

**2. Check APNs:**
```swift
func application(_ application: UIApplication,
                 didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data) {
    print("APNs device token: \(deviceToken)")
}
```

**3. Check GoogleService-Info.plist:**
- Added to Xcode project
- Bundle ID matches

### Token Not Sent to Backend

**Check:**
1. Token saved locally
2. Network connection
3. API endpoint correct
4. Request format correct

**Debug:**
```java
// Android
String token = getSharedPreferences("FCM", MODE_PRIVATE)
    .getString("token", null);
Log.d("FCM", "Saved token: " + token);
```

```swift
// iOS
let token = UserDefaults.standard.string(forKey: "fcm_token")
print("Saved token: \(token ?? "none")")
```

### Backend Not Sending Notification

**Check:**
1. Admin has FCM tokens in database
2. Firebase credentials correct
3. Backend logs for errors
4. Token format valid

**Debug:**
```python
# Check admin FCM tokens
admin = await mongodb.db.admins.find_one({"username": "admin"})
print(f"FCM Tokens: {admin.get('fcm_tokens', [])}")
```

---

## Summary

### Complete Flow

1. **App Starts** ? Initialize Firebase ? Get FCM token
2. **Admin Logs In** ? Send FCM token to backend (in `/auth/verify-2fa`)
3. **Backend Saves Token** ? Store in `admins.fcm_tokens` array
4. **New Device Registers** ? Backend sends notification via Firebase
5. **Admin Receives Notification** ? Show notification ? Handle tap

### Key Points

? **Get FCM token on app start**  
? **Send token during login** (Step 2 of 2FA)  
? **Handle foreground notifications** (show even when app is open)  
? **Handle background notifications** (system shows automatically)  
? **Handle notification tap** (navigate to relevant screen)  
? **Update token on refresh** (token can change)  
? **Test thoroughly** (foreground, background, quit state)  

---

**Last Updated:** November 2, 2025  
**Version:** 2.0.0
