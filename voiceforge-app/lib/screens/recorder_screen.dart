import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter_sound/flutter_sound.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

class RecorderScreen extends StatefulWidget {
  const RecorderScreen({super.key});

  @override
  State<RecorderScreen> createState() => _RecorderScreenState();
}

class _RecorderScreenState extends State<RecorderScreen> {
  static const _defaultWsUrl = 'ws://10.0.2.2:8000/stream/transcribe';

  final FlutterSoundRecorder _recorder = FlutterSoundRecorder();
  final TextEditingController _wsUrlController = TextEditingController(text: _defaultWsUrl);

  WebSocketChannel? _channel;
  StreamSubscription? _wsSub;

  StreamController<Uint8List>? _pcmStream;
  StreamSubscription<Uint8List>? _pcmSub;

  bool _isRecording = false;
  bool _wsReady = false;
  bool _isConnecting = false;
  String? _wsError;

  String _liveTranscript = '';
  Map<String, dynamic>? _finalIntelligence;

  @override
  void initState() {
    super.initState();
    unawaited(_initRecorder());
  }

  Future<void> _initRecorder() async {
    await _recorder.openRecorder();
  }

  @override
  void dispose() {
    unawaited(_stop());
    _wsUrlController.dispose();
    unawaited(_recorder.closeRecorder());
    super.dispose();
  }

  String _normalizeWsUrl(String raw) {
    final trimmed = raw.trim();
    if (trimmed.isEmpty) {
      return trimmed;
    }

    if (!trimmed.contains('://')) {
      return 'ws://$trimmed';
    }
    if (trimmed.startsWith('http://')) {
      return 'ws://${trimmed.substring('http://'.length)}';
    }
    if (trimmed.startsWith('https://')) {
      return 'wss://${trimmed.substring('https://'.length)}';
    }
    return trimmed;
  }

  void _showError(String message) {
    if (!mounted) {
      return;
    }
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message)),
    );
  }

  Future<void> _connect() async {
    if (_channel != null || _isConnecting) {
      return;
    }

    final normalized = _normalizeWsUrl(_wsUrlController.text);
    if (normalized != _wsUrlController.text) {
      _wsUrlController.text = normalized;
    }

    Uri url;
    try {
      url = Uri.parse(normalized);
    } catch (_) {
      _showError('Invalid WebSocket URL');
      return;
    }

    if (url.scheme != 'ws' && url.scheme != 'wss') {
      _showError('WebSocket URL must start with ws:// or wss://');
      return;
    }

    setState(() {
      _isConnecting = true;
      _wsError = null;
      _wsReady = false;
      _finalIntelligence = null;
      _liveTranscript = '';
    });

    WebSocketChannel channel;
    try {
      channel = WebSocketChannel.connect(url);
    } catch (e) {
      _setDisconnected(error: 'WebSocket connection failed: $e');
      return;
    }

    final sub = channel.stream.listen(
      (event) {
        if (event is String) {
          _handleServerEvent(event);
        }
      },
      onError: (_) {
        _setDisconnected(error: 'WebSocket error');
      },
      onDone: () {
        _setDisconnected(error: 'WebSocket disconnected');
      },
    );

    setState(() {
      _channel = channel;
      _wsSub = sub;
      _isConnecting = false;
    });
  }

  void _setDisconnected({String? error}) {
    setState(() {
      _wsReady = false;
      _isConnecting = false;
      _isRecording = false;
      _wsError = error;
    });

    if (error != null && error.isNotEmpty) {
      _showError(error);
    }

    unawaited(() async {
      try {
        await _recorder.stopRecorder();
      } catch (_) {}
    }());

    unawaited(_wsSub?.cancel());
    _wsSub = null;
    unawaited(_channel?.sink.close());
    _channel = null;
  }

  void _handleServerEvent(String message) {
    final obj = jsonDecode(message);
    if (obj is! Map<String, dynamic>) {
      return;
    }

    final event = obj['event'];
    if (event == 'ready') {
      setState(() {
        _wsReady = true;
        _isConnecting = false;
      });
      return;
    }

    if (event == 'partial_transcript') {
      final clean = obj['clean_transcript'];
      if (clean is String) {
        setState(() {
          _liveTranscript = clean;
        });
      }
      return;
    }

    if (event == 'final') {
      final intelligence = obj['intelligence'];
      setState(() {
        _finalIntelligence = intelligence is Map<String, dynamic> ? intelligence : null;
      });
      return;
    }
  }

  Future<void> _start() async {
    if (_channel == null || !_wsReady) {
      _showError('Connect to the backend first.');
      return;
    }

    final status = await Permission.microphone.request();
    if (status.isPermanentlyDenied) {
      _showError('Microphone permission is permanently denied. Enable it in Settings.');
      await openAppSettings();
      return;
    }
    if (!status.isGranted) {
      _showError('Microphone permission is required to record.');
      return;
    }

    _pcmStream = StreamController<Uint8List>();
    _pcmSub = _pcmStream!.stream.listen((bytes) {
      if (bytes.isEmpty) {
        return;
      }

      final channel = _channel;
      if (channel == null) {
        return;
      }

      channel.sink.add(bytes);
    });

    await _recorder.startRecorder(
      codec: Codec.pcm16,
      numChannels: 1,
      sampleRate: 16000,
      toStream: _pcmStream!.sink,
    );

    setState(() {
      _isRecording = true;
      _finalIntelligence = null;
      _liveTranscript = '';
    });
  }

  Future<void> _stop() async {
    if (!_isRecording) {
      await _disconnect();
      return;
    }

    await _recorder.stopRecorder();

    final channel = _channel;
    if (channel != null) {
      channel.sink.add(jsonEncode({'event': 'flush'}));
    }

    await _pcmSub?.cancel();
    _pcmSub = null;
    await _pcmStream?.close();
    _pcmStream = null;

    setState(() {
      _isRecording = false;
    });
  }

  Future<void> _disconnect() async {
    await _wsSub?.cancel();
    _wsSub = null;
    await _channel?.sink.close();
    _channel = null;

    setState(() {
      _wsReady = false;
      _isConnecting = false;
      _wsError = null;
    });
  }

  Widget _buildSummaryCard() {
    final intel = _finalIntelligence;
    if (intel == null) {
      return const SizedBox.shrink();
    }

    final summary = intel['summary'];
    final intent = intel['intent'];
    final actionItems = intel['action_items'];

    final items = actionItems is List ? actionItems : const [];

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('AI Intelligence', style: TextStyle(fontWeight: FontWeight.w600)),
            const SizedBox(height: 8),
            Text('Summary: ${summary ?? ''}'),
            const SizedBox(height: 6),
            Text('Intent: ${intent ?? ''}'),
            const SizedBox(height: 10),
            const Text('Action items', style: TextStyle(fontWeight: FontWeight.w600)),
            const SizedBox(height: 6),
            if (items.isEmpty) const Text('None'),
            for (final item in items)
              if (item is Map<String, dynamic>)
                Padding(
                  padding: const EdgeInsets.only(bottom: 6),
                  child: Text('- ${item['description'] ?? ''}'),
                ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final wsOk = _channel != null && _wsReady;
    final statusText = wsOk
        ? 'Connected'
        : (_isConnecting ? 'Connecting…' : 'Disconnected');
    final statusColor = wsOk ? Colors.green : (_isConnecting ? Colors.orange : Colors.red);
    final canConnect = !wsOk && !_isConnecting;

    return Scaffold(
      appBar: AppBar(
        title: const Text('VoiceForge AI'),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            TextField(
              controller: _wsUrlController,
              decoration: const InputDecoration(
                labelText: 'WebSocket URL',
                hintText: _defaultWsUrl,
              ),
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Container(
                  width: 10,
                  height: 10,
                  decoration: BoxDecoration(color: statusColor, shape: BoxShape.circle),
                ),
                const SizedBox(width: 8),
                Text('Status: $statusText'),
              ],
            ),
            if (_wsError != null) ...[
              const SizedBox(height: 6),
              Text(
                _wsError!,
                style: const TextStyle(color: Colors.red),
              ),
            ],
            const SizedBox(height: 8),
            const Text(
              'Emulator: ws://10.0.2.2:8000/stream/transcribe\nDevice: ws://<LAN-IP>:8000/stream/transcribe',
              style: TextStyle(color: Colors.black54, fontSize: 12),
            ),
            const SizedBox(height: 12),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Live transcript', style: TextStyle(fontWeight: FontWeight.w600)),
                    const SizedBox(height: 8),
                    Text(_liveTranscript.isEmpty ? '—' : _liveTranscript),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 12),
            _buildSummaryCard(),
            const Spacer(),
            GestureDetector(
              onLongPressStart: (_) {
                if (!_isRecording && wsOk) {
                  unawaited(_start());
                }
              },
              onLongPressEnd: (_) {
                if (_isRecording) {
                  unawaited(_stop());
                }
              },
              child: ElevatedButton(
                onPressed: canConnect ? () => unawaited(_connect()) : null,
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                ),
                child: Text(
                  _isRecording
                      ? 'Recording… release to send'
                      : (wsOk ? 'Hold to record' : (_isConnecting ? 'Connecting…' : 'Connect')),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
