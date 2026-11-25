import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:path_provider/path_provider.dart';
import 'package:record/record.dart';
import 'package:permission_handler/permission_handler.dart';
import '../services/api_service.dart';
import '../services/localization.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final TextEditingController _textController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final MandiApiService _apiService = MandiApiService();
  final ImagePicker _picker = ImagePicker();

  // Message format: {'role': 'user' | 'bot', 'text': String, 'image': String?, 'audio': String?}
  final List<Map<String, dynamic>> _messages = [];
  bool _isLoading = false;
  File? _selectedImage;

  final AudioRecorder _audioRecorder = AudioRecorder();
  bool _isRecording = false;

  @override
  void dispose() {
    _audioRecorder.dispose();
    super.dispose();
  }

  Future<void> _startRecording() async {
    try {
      if (await Permission.microphone.request().isGranted) {
        final dir = await getApplicationDocumentsDirectory();
        final path =
            '${dir.path}/audio_${DateTime.now().millisecondsSinceEpoch}.m4a';
        await _audioRecorder.start(
          const RecordConfig(encoder: AudioEncoder.aacLc),
          path: path,
        );
        setState(() {
          _isRecording = true;
        });
      }
    } catch (e) {
      debugPrint("Error starting record: $e");
    }
  }

  Future<void> _stopRecording() async {
    try {
      final path = await _audioRecorder.stop();
      setState(() {
        _isRecording = false;
      });
      if (path != null) {
        // Automatically send audio message when recording stops
        _sendAudioMessage(path);
      }
    } catch (e) {
      debugPrint("Error stopping record: $e");
    }
  }

  Future<void> _sendAudioMessage(String audioPath) async {
    setState(() {
      _messages.add({
        'role': 'user',
        'text': '🎤 Audio Message sent',
        'image': null,
        'audio': audioPath
      });
      _isLoading = true;
    });
    _scrollToBottom();

    try {
      final response =
          await _apiService.sendChat("", null, audioPath: audioPath);
      setState(() {
        _messages.add({'role': 'bot', 'text': response});
      });
    } catch (e) {
      setState(() {
        _messages.add({
          'role': 'bot',
          'text':
              "${AppLocalizations.get(localeNotifier.value, 'error_connect')}\n($e)",
        });
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
      _scrollToBottom();
    }
  }

  Future<void> _pickImage() async {
    final XFile? image = await _picker.pickImage(source: ImageSource.gallery);
    if (image != null) {
      setState(() {
        _selectedImage = File(image.path);
      });
    }
  }

  Future<void> _pickImageCamera() async {
    final XFile? image = await _picker.pickImage(source: ImageSource.camera);
    if (image != null) {
      setState(() {
        _selectedImage = File(image.path);
      });
    }
  }

  void _showImagePickerModal() {
    showModalBottomSheet(
      context: context,
      builder: (context) => SafeArea(
        child: Wrap(
          children: <Widget>[
            ListTile(
              leading: const Icon(Icons.photo_library),
              title:
                  Text(AppLocalizations.get(localeNotifier.value, 'gallery')),
              onTap: () {
                Navigator.of(context).pop();
                _pickImage();
              },
            ),
            ListTile(
              leading: const Icon(Icons.photo_camera),
              title: Text(AppLocalizations.get(localeNotifier.value, 'camera')),
              onTap: () {
                Navigator.of(context).pop();
                _pickImageCamera();
              },
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _sendMessage() async {
    if (_textController.text.trim().isEmpty && _selectedImage == null) return;

    final String text = _textController.text.trim();
    final String? imagePath =
        _selectedImage?.path; // Store before clearing state

    setState(() {
      _messages.add({'role': 'user', 'text': text, 'image': imagePath});
      _isLoading = true;
      _textController.clear();
      _selectedImage = null; // Clear image after sending
    });
    _scrollToBottom();

    try {
      // If user sends only image, add a default prompt
      String prompt = text.isEmpty ? "What is this? Explain in detail." : text;

      final response = await _apiService.sendChat(prompt, imagePath);

      setState(() {
        _messages.add({'role': 'bot', 'text': response});
      });
    } catch (e) {
      setState(() {
        _messages.add({
          'role': 'bot',
          'text':
              "${AppLocalizations.get(localeNotifier.value, 'error_connect')}\n($e)",
        });
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
      _scrollToBottom();
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<String>(
      valueListenable: localeNotifier,
      builder: (context, locale, child) {
        return Scaffold(
          appBar: AppBar(
            title: Text(AppLocalizations.get(locale, 'field_assistant')),
            backgroundColor: Colors.green,
            elevation: 0,
          ),
          body: Column(
            children: [
              // Chat List
              Expanded(
                child: ListView.builder(
                  controller: _scrollController,
                  padding: const EdgeInsets.all(16),
                  itemCount: _messages.length,
                  itemBuilder: (context, index) {
                    final msg = _messages[index];
                    final isUser = msg['role'] == 'user';

                    return Align(
                      alignment:
                          isUser ? Alignment.centerRight : Alignment.centerLeft,
                      child: Container(
                        margin: const EdgeInsets.symmetric(vertical: 8),
                        constraints: BoxConstraints(
                          maxWidth: MediaQuery.of(context).size.width * 0.8,
                        ),
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: isUser ? Colors.green[100] : Colors.white,
                          borderRadius: BorderRadius.only(
                            topLeft: const Radius.circular(12),
                            topRight: const Radius.circular(12),
                            bottomLeft: isUser
                                ? const Radius.circular(12)
                                : Radius.zero,
                            bottomRight: isUser
                                ? Radius.zero
                                : const Radius.circular(12),
                          ),
                          boxShadow: [
                            BoxShadow(
                              color: Colors.grey.withValues(alpha: 0.2),
                              spreadRadius: 1,
                              blurRadius: 2,
                              offset: const Offset(0, 1),
                            ),
                          ],
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            // Display User Image if sent
                            if (msg['image'] != null)
                              Padding(
                                padding: const EdgeInsets.only(bottom: 8.0),
                                child: ClipRRect(
                                  borderRadius: BorderRadius.circular(8),
                                  child: Image.file(
                                    File(msg['image']),
                                    height: 150,
                                    width: double.infinity,
                                    fit: BoxFit.cover,
                                  ),
                                ),
                              ),

                            // Text Content (Markdown for Bot, Plain for User)
                            if (isUser)
                              Text(
                                msg['text'],
                                style: const TextStyle(fontSize: 16),
                              )
                            else
                              MarkdownBody(
                                data: msg['text'],
                                styleSheet: MarkdownStyleSheet(
                                  p: const TextStyle(fontSize: 16),
                                ),
                              ),
                          ],
                        ),
                      ),
                    );
                  },
                ),
              ),

              if (_isLoading)
                const Padding(
                  padding: EdgeInsets.all(8.0),
                  child: LinearProgressIndicator(color: Colors.green),
                ),

              // Input Area
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Colors.white,
                  boxShadow: [
                    BoxShadow(
                      color: Colors.grey.withValues(alpha: 0.2),
                      spreadRadius: 1,
                      blurRadius: 4,
                      offset: const Offset(0, -1),
                    ),
                  ],
                ),
                child: SafeArea(
                  child: Column(
                    children: [
                      if (_selectedImage != null)
                        Container(
                          padding: const EdgeInsets.all(8),
                          color: Colors.grey[100],
                          child: Row(
                            children: [
                              const Icon(Icons.image, color: Colors.green),
                              const SizedBox(width: 8),
                              Expanded(
                                child: Text(
                                  AppLocalizations.get(
                                      locale, 'image_selected'),
                                  style: TextStyle(color: Colors.grey[800]),
                                ),
                              ),
                              IconButton(
                                icon: const Icon(
                                  Icons.close,
                                ),
                                onPressed: () {
                                  setState(() {
                                    _selectedImage = null;
                                  });
                                },
                              ),
                            ],
                          ),
                        ),
                      Row(
                        children: [
                          IconButton(
                            icon: const Icon(
                              Icons.add_photo_alternate,
                              color: Colors.green,
                            ),
                            onPressed: _showImagePickerModal,
                          ),
                          IconButton(
                            icon: Icon(
                              _isRecording ? Icons.stop_circle : Icons.mic,
                              color: _isRecording ? Colors.red : Colors.green,
                            ),
                            onPressed: () {
                              if (_isRecording) {
                                _stopRecording();
                              } else {
                                _startRecording();
                              }
                            },
                          ),
                          Expanded(
                            child: TextField(
                              controller: _textController,
                              decoration: InputDecoration(
                                hintText: AppLocalizations.get(
                                  locale,
                                  'ask_assistant',
                                ),
                                border: OutlineInputBorder(
                                  borderRadius: BorderRadius.circular(24),
                                  borderSide: BorderSide.none,
                                ),
                                filled: true,
                                fillColor: Colors.grey[100],
                                contentPadding: const EdgeInsets.symmetric(
                                  horizontal: 16,
                                  vertical: 8,
                                ),
                              ),
                              minLines: 1,
                              maxLines: 4,
                            ),
                          ),
                          const SizedBox(width: 8),
                          CircleAvatar(
                            backgroundColor: Colors.green,
                            child: IconButton(
                              icon: const Icon(Icons.send, color: Colors.white),
                              onPressed: _sendMessage,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}
