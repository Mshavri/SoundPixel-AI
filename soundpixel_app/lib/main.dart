import 'dart:io';
import 'dart:typed_data';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:file_picker/file_picker.dart';
import 'package:http/http.dart' as http;
import 'package:audioplayers/audioplayers.dart';
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';
import 'package:gal/gal.dart';

void main() => runApp(const SoundPixelApp());

// ─────────────────────────────────────────────────────────────────────────────
// Global configuration — editable at runtime via Settings
// ─────────────────────────────────────────────────────────────────────────────
class AppConfig {
  static String serverUrl = 'http://192.168.1.57:8000';
}

class SoundPixelApp extends StatelessWidget {
  const SoundPixelApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      theme: ThemeData.dark().copyWith(
        scaffoldBackgroundColor: const Color(0xFF0A0C10),
        useMaterial3: true,
      ),
      home: const HomePage(),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// HOME PAGE
// ─────────────────────────────────────────────────────────────────────────────
class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  void _showServerSettings() {
    final controller = TextEditingController(text: AppConfig.serverUrl);
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF161B22),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Text(
          'Server Settings',
          style: TextStyle(color: Colors.white, fontSize: 16),
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Backend URL',
              style: TextStyle(
                  color: Colors.white.withOpacity(0.5), fontSize: 12),
            ),
            const SizedBox(height: 8),
            TextField(
              controller: controller,
              style: const TextStyle(color: Colors.white, fontSize: 14),
              decoration: InputDecoration(
                hintText: 'http://192.168.x.x:8000',
                hintStyle:
                    TextStyle(color: Colors.white.withOpacity(0.3)),
                enabledBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(8),
                  borderSide: const BorderSide(color: Colors.white24),
                ),
                focusedBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(8),
                  borderSide:
                      const BorderSide(color: Color(0xFF4A90E2)),
                ),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child:
                const Text('Cancel', style: TextStyle(color: Colors.grey)),
          ),
          ElevatedButton(
            onPressed: () {
              final url = controller.text.trim();
              if (url.isNotEmpty) {
                AppConfig.serverUrl = url;
                setState(() {});
              }
              Navigator.pop(ctx);
            },
            style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF4A90E2)),
            child: const Text('Save',
                style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(20.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 10),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'SOUNDPIXEL',
                        style: TextStyle(
                          fontSize: 24,
                          fontWeight: FontWeight.w600,
                          color: Colors.white,
                          letterSpacing: 4,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'Encrypted Audio Messaging',
                        style: TextStyle(
                          fontSize: 13,
                          color: Colors.white.withOpacity(0.4),
                        ),
                      ),
                    ],
                  ),
                  IconButton(
                    icon: Icon(
                      Icons.settings_outlined,
                      color: Colors.white.withOpacity(0.4),
                    ),
                    onPressed: _showServerSettings,
                    tooltip: 'Server Settings',
                  ),
                ],
              ),
              const SizedBox(height: 30),
              Expanded(
                flex: 1,
                child: _menuCard(
                  context,
                  'SENDER',
                  'Image → Encrypted Audio',
                  Icons.lock_outline,
                  const Color(0xFF4A90E2),
                  const SenderScreen(),
                ),
              ),
              const SizedBox(height: 16),
              Expanded(
                flex: 1,
                child: _menuCard(
                  context,
                  'RECEIVER',
                  'Audio → Decrypted Image',
                  Icons.lock_open_outlined,
                  const Color(0xFF50E3C2),
                  const ReceiverScreen(),
                ),
              ),
              const SizedBox(height: 16),
              Center(
                child: Text(
                  'Share encrypted audio • Receive and decrypt',
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.white.withOpacity(0.3),
                  ),
                ),
              ),
              const SizedBox(height: 10),
            ],
          ),
        ),
      ),
    );
  }

  Widget _menuCard(BuildContext context, String title, String subtitle,
      IconData icon, Color color, Widget screen) {
    return GestureDetector(
      onTap: () =>
          Navigator.push(context, MaterialPageRoute(builder: (_) => screen)),
      child: Container(
        width: double.infinity,
        decoration: BoxDecoration(
          color: const Color(0xFF161B22),
          borderRadius: BorderRadius.circular(24),
          border: Border.all(color: color.withOpacity(0.5), width: 2),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 50, color: color),
            const SizedBox(height: 15),
            Text(
              title,
              style: const TextStyle(
                fontSize: 22,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              subtitle,
              style: TextStyle(
                fontSize: 14,
                color: Colors.white.withOpacity(0.5),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// SENDER SCREEN
// ─────────────────────────────────────────────────────────────────────────────
class SenderScreen extends StatefulWidget {
  const SenderScreen({super.key});

  @override
  State<SenderScreen> createState() => _SenderScreenState();
}

class _SenderScreenState extends State<SenderScreen> {
  File? _image;
  bool _isLoading = false;
  Uint8List? _audioBytes;

  Future<void> _process() async {
    if (_image == null) return;
    setState(() => _isLoading = true);

    try {
      final url = '${AppConfig.serverUrl}/sender/process';
      var request = http.MultipartRequest('POST', Uri.parse(url));
      request.files
          .add(await http.MultipartFile.fromPath('file', _image!.path));

      final response = await request
          .send()
          .timeout(const Duration(minutes: 5));

      if (response.statusCode == 200) {
        _audioBytes = await response.stream.toBytes();
        if (!mounted) return;
        setState(() => _isLoading = false);
        _showAudioDialog();
      } else {
        final body = await response.stream.bytesToString();
        throw Exception(
            'Server error ${response.statusCode}: $body');
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isLoading = false);
        _showError('$e');
      }
    }
  }

  void _showAudioDialog() {
    showDialog(
      context: context,
      builder: (_) => AudioPlayerDialog(audioBytes: _audioBytes!),
    );
  }

  void _showError(String msg) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(
      content: Text(msg, style: const TextStyle(fontSize: 13)),
      backgroundColor: Colors.red.shade800,
      duration: const Duration(seconds: 5),
    ));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0C10),
      appBar: AppBar(
        title: const Text('SENDER',
            style: TextStyle(color: Colors.white, letterSpacing: 2)),
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Select image',
              style: TextStyle(
                  fontSize: 13, color: Colors.white.withOpacity(0.4)),
            ),
            const SizedBox(height: 16),
            Expanded(
              child: Container(
                width: double.infinity,
                decoration: BoxDecoration(
                  color: const Color(0xFF14181F),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: _image == null
                    ? Center(
                        child: Text(
                          'No image selected',
                          style: TextStyle(
                              color: Colors.white.withOpacity(0.3),
                              fontSize: 14),
                        ),
                      )
                    : ClipRRect(
                        borderRadius: BorderRadius.circular(12),
                        child: Image.file(_image!, fit: BoxFit.contain),
                      ),
              ),
            ),
            const SizedBox(height: 20),
            SizedBox(
              width: double.infinity,
              height: 52,
              child: ElevatedButton(
                onPressed: () async {
                  final img = await ImagePicker()
                      .pickImage(source: ImageSource.gallery);
                  if (img != null) setState(() => _image = File(img.path));
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF4A90E2),
                  shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12)),
                  elevation: 0,
                ),
                child: const Text('Pick Image',
                    style: TextStyle(fontSize: 15, color: Colors.white)),
              ),
            ),
            const SizedBox(height: 10),
            SizedBox(
              width: double.infinity,
              height: 52,
              child: ElevatedButton(
                onPressed: _isLoading ? null : _process,
                style: ElevatedButton.styleFrom(
                  backgroundColor: _image == null
                      ? Colors.grey.shade800
                      : const Color(0xFF50E3C2),
                  shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12)),
                  elevation: 0,
                ),
                child: _isLoading
                    ? const SizedBox(
                        width: 22,
                        height: 22,
                        child: CircularProgressIndicator(
                            color: Colors.white, strokeWidth: 2))
                    : const Text('Convert to Sound',
                        style: TextStyle(
                            fontSize: 15, color: Colors.black)),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// AUDIO PLAYER DIALOG
// ─────────────────────────────────────────────────────────────────────────────
class AudioPlayerDialog extends StatefulWidget {
  final Uint8List audioBytes;
  const AudioPlayerDialog({super.key, required this.audioBytes});

  @override
  State<AudioPlayerDialog> createState() => _AudioPlayerDialogState();
}

class _AudioPlayerDialogState extends State<AudioPlayerDialog> {
  final AudioPlayer _player = AudioPlayer();
  bool isPlaying = false;
  File? _audioFile;

  @override
  void initState() {
    super.initState();
    _player.onPlayerComplete.listen((_) {
      if (mounted) setState(() => isPlaying = false);
    });
    _prepareAudioFile();
  }

  Future<void> _prepareAudioFile() async {
    final dir = await getTemporaryDirectory();
    _audioFile = File('${dir.path}/soundpixel_output.wav');
    await _audioFile!.writeAsBytes(widget.audioBytes);
  }

  void _togglePlay() async {
    if (isPlaying) {
      await _player.pause();
    } else {
      await _player.play(BytesSource(widget.audioBytes));
    }
    setState(() => isPlaying = !isPlaying);
  }

  @override
  void dispose() {
    _player.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      backgroundColor: const Color(0xFF161B22),
      shape:
          RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      title:
          const Text('Audio Ready', style: TextStyle(color: Colors.white)),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const SizedBox(height: 10),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              IconButton(
                icon: Icon(
                  isPlaying
                      ? Icons.pause_circle_filled
                      : Icons.play_circle_filled,
                  size: 52,
                  color: const Color(0xFF4A90E2),
                ),
                onPressed: _togglePlay,
              ),
            ],
          ),
          const SizedBox(height: 10),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('Close', style: TextStyle(color: Colors.grey)),
        ),
        ElevatedButton.icon(
          onPressed: () async {
            if (_audioFile != null) {
              await Share.shareXFiles([XFile(_audioFile!.path)]);
            }
          },
          icon: const Icon(Icons.share, size: 16),
          label: const Text('Share'),
          style: ElevatedButton.styleFrom(
            backgroundColor: const Color(0xFF4A90E2),
            foregroundColor: Colors.white,
          ),
        ),
      ],
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// RECEIVER SCREEN
// ─────────────────────────────────────────────────────────────────────────────
class ReceiverScreen extends StatefulWidget {
  const ReceiverScreen({super.key});

  @override
  State<ReceiverScreen> createState() => _ReceiverScreenState();
}

class _ReceiverScreenState extends State<ReceiverScreen> {
  bool _isLoading = false;

  Future<void> _upload() async {
    final res =
        await FilePicker.platform.pickFiles(type: FileType.audio);
    if (res == null) return;

    setState(() => _isLoading = true);

    try {
      final url = '${AppConfig.serverUrl}/receiver/process';
      var request = http.MultipartRequest('POST', Uri.parse(url));
      request.files.add(await http.MultipartFile.fromPath(
          'file', res.files.single.path!));

      final response = await request
          .send()
          .timeout(const Duration(minutes: 5));

      if (response.statusCode == 200) {
        final bytes = await response.stream.toBytes();
        if (!mounted) return;
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (_) => ReceiverResultPage(
              imageBytes: bytes,
              audioFileName: res.files.single.name,
            ),
          ),
        );
      } else {
        final body = await response.stream.bytesToString();
        throw Exception(
            'Server error ${response.statusCode}: $body');
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text('Error: $e',
              style: const TextStyle(fontSize: 13)),
          backgroundColor: Colors.red.shade800,
          duration: const Duration(seconds: 5),
        ));
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  void _showRecordComingSoon() {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF161B22),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Row(children: [
          Icon(Icons.mic_off_outlined, color: Color(0xFF50E3C2), size: 20),
          SizedBox(width: 8),
          Text('Not Available Yet', style: TextStyle(color: Colors.white, fontSize: 15)),
        ]),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Live recording isn\'t supported yet because the app '
              'needs a specific audio format (WAV) that microphone '
              'libraries don\'t produce directly on all phones.',
              style: TextStyle(color: Colors.white.withOpacity(0.75), fontSize: 13, height: 1.5),
            ),
            const SizedBox(height: 14),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
              decoration: BoxDecoration(
                color: const Color(0xFF50E3C2).withOpacity(0.08),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: const Color(0xFF50E3C2).withOpacity(0.25)),
              ),
              child: Row(children: [
                const Icon(Icons.upload_file, color: Color(0xFF50E3C2), size: 16),
                const SizedBox(width: 8),
                Expanded(child: Text(
                  'Use Upload to select a .wav file you received.',
                  style: TextStyle(color: const Color(0xFF50E3C2).withOpacity(0.9), fontSize: 12),
                )),
              ]),
            ),
          ],
        ),
        actions: [
          ElevatedButton(
            onPressed: () => Navigator.pop(ctx),
            style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF50E3C2)),
            child: const Text('Got it', style: TextStyle(color: Colors.black, fontWeight: FontWeight.w600)),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0C10),
      appBar: AppBar(
        title: const Text('RECEIVER',
            style: TextStyle(color: Colors.white, letterSpacing: 2)),
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Ready to receive',
              style: TextStyle(
                  fontSize: 13, color: Colors.white.withOpacity(0.4)),
            ),
            const SizedBox(height: 16),
            Expanded(
              child: Container(
                width: double.infinity,
                decoration: BoxDecoration(
                  color: const Color(0xFF14181F),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(
                        _isLoading
                            ? Icons.hourglass_top
                            : Icons.mic_none_outlined,
                        size: 60,
                        color: _isLoading
                            ? const Color(0xFF4A90E2).withOpacity(0.7)
                            : const Color(0xFF50E3C2).withOpacity(0.5),
                      ),
                      const SizedBox(height: 16),
                      Text(
                        _isLoading ? 'Processing...' : 'Listening...',
                        style: TextStyle(
                          color: Colors.white.withOpacity(0.3),
                          fontSize: 14,
                        ),
                      ),
                      const SizedBox(height: 20),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: List.generate(14, (i) {
                          return AnimatedContainer(
                            duration:
                                const Duration(milliseconds: 200),
                            width: 3,
                            height: _isLoading
                                ? 10.0 + (i % 7) * 6
                                : 14.0 + (i % 4) * 6,
                            margin: const EdgeInsets.symmetric(
                                horizontal: 3),
                            decoration: BoxDecoration(
                              color: const Color(0xFF50E3C2)
                                  .withOpacity(0.3 + (i * 0.04)),
                              borderRadius: BorderRadius.circular(2),
                            ),
                          );
                        }),
                      ),
                    ],
                  ),
                ),
              ),
            ),
            const SizedBox(height: 20),
            Row(
              children: [
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: _isLoading ? null : _upload,
                    icon: const Icon(Icons.upload_file, size: 18),
                    label: const Text('Upload'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF4A90E2),
                      shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12)),
                      elevation: 0,
                      padding:
                          const EdgeInsets.symmetric(vertical: 14),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: _showRecordComingSoon,
                    icon: const Icon(Icons.mic, size: 18),
                    label: const Text('Record'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor:
                          const Color(0xFF50E3C2).withOpacity(0.35),
                      foregroundColor: Colors.white54,
                      shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12)),
                      elevation: 0,
                      padding:
                          const EdgeInsets.symmetric(vertical: 14),
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// RECEIVER RESULT SCREEN
// ─────────────────────────────────────────────────────────────────────────────
class ReceiverResultPage extends StatefulWidget {
  final Uint8List imageBytes;
  final String audioFileName;

  const ReceiverResultPage(
      {super.key,
      required this.imageBytes,
      required this.audioFileName});

  @override
  State<ReceiverResultPage> createState() => _ReceiverResultPageState();
}

class _ReceiverResultPageState extends State<ReceiverResultPage> {
  Map<String, dynamic>? _reportData;
  bool _isLoadingReport = false;
  bool _isSaving        = false;

  // ── Save to gallery via gal ────────────────────────────────────────────────
  Future<void> _saveImage() async {
    if (_isSaving) return;
    setState(() => _isSaving = true);
    try {
      await Gal.putImageBytes(widget.imageBytes, name: 'soundpixel_${DateTime.now().millisecondsSinceEpoch}');

      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: const Row(children: [
            Icon(Icons.check_circle, color: Colors.black, size: 18),
            SizedBox(width: 10),
            Expanded(
              child: Text('Saved to Gallery',
                  style: TextStyle(
                      color: Colors.black,
                      fontSize: 13,
                      fontWeight: FontWeight.w500)),
            ),
          ]),
          backgroundColor: const Color(0xFF50E3C2),
          duration: const Duration(seconds: 3),
          behavior: SnackBarBehavior.floating,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text('Save failed: $e', style: const TextStyle(fontSize: 13)),
        backgroundColor: Colors.red.shade800,
        duration: const Duration(seconds: 4),
      ));
    } finally {
      if (mounted) setState(() => _isSaving = false);
    }
  }

  // ── Fetch report ────────────────────────────────────────────────────────────
  Future<void> _fetchReport() async {
    setState(() => _isLoadingReport = true);
    try {
      final url = '${AppConfig.serverUrl}/receiver/report/latest';
      final response = await http
          .get(Uri.parse(url))
          .timeout(const Duration(seconds: 10));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        _reportData = data;
        final hasRealData = data['mse'] != null &&
            data['psnr'] != null &&
            data['quality_status'] != null &&
            data['quality_status'] != 'Unknown';
        if (mounted) {
          if (hasRealData) _showReportDialog(); else _showNoDataDialog();
        }
      } else {
        if (mounted) _showNoDataDialog();
      }
    } catch (_) {
      if (mounted) _showNoDataDialog();
    } finally {
      if (mounted) setState(() => _isLoadingReport = false);
    }
  }

  void _showReportDialog() {
    if (_reportData == null) return;
    final data    = _reportData!;
    final quality = (data['quality_status'] as String?) ?? 'Unknown';
    final mse     = data['mse'];
    final psnr    = data['psnr'];

    final qualityColor = switch (quality) {
      'Excellent' => const Color(0xFF4CAF50),
      'Good'      => const Color(0xFF8BC34A),
      'Fair'      => const Color(0xFFFFA726),
      'Poor'      => const Color(0xFFEF5350),
      _           => Colors.white,
    };

    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF161B22),
      shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (_) => Padding(
        padding: const EdgeInsets.fromLTRB(22, 22, 22, 30),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text('Quality Report',
                style: TextStyle(color: Colors.white, fontSize: 17, fontWeight: FontWeight.w700)),
            const SizedBox(height: 16),
            const Divider(color: Colors.white12),
            const SizedBox(height: 14),
            Row(children: [
              Expanded(child: _metricCard(label: 'MSE',  value: mse?.toString()            ?? '—', sub: 'Mean Square Error',    color: const Color(0xFF4A90E2))),
              const SizedBox(width: 12),
              Expanded(child: _metricCard(label: 'PSNR', value: psnr != null ? '$psnr dB' : '—', sub: 'Peak Signal-to-Noise', color: const Color(0xFF50E3C2))),
            ]),
            const SizedBox(height: 16),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(vertical: 14),
              decoration: BoxDecoration(
                color: qualityColor.withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: qualityColor.withOpacity(0.35)),
              ),
              child: Column(children: [
                Text(quality, style: TextStyle(color: qualityColor, fontSize: 22, fontWeight: FontWeight.w700, letterSpacing: 1)),
                const SizedBox(height: 2),
                Text('Reconstruction Quality', style: TextStyle(color: qualityColor.withOpacity(0.7), fontSize: 11)),
              ]),
            ),
            const SizedBox(height: 20),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () => Navigator.pop(context),
                style: ElevatedButton.styleFrom(backgroundColor: Colors.white10, padding: const EdgeInsets.symmetric(vertical: 14)),
                child: const Text('Close', style: TextStyle(color: Colors.white70)),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _metricCard({required String label, required String value, required String sub, required Color color}) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: color.withOpacity(0.08),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withOpacity(0.2)),
      ),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(label, style: TextStyle(color: color, fontSize: 11, fontWeight: FontWeight.w600, letterSpacing: 1)),
        const SizedBox(height: 4),
        Text(value, style: const TextStyle(color: Colors.white, fontSize: 17, fontWeight: FontWeight.w700, fontFamily: 'monospace')),
        const SizedBox(height: 2),
        Text(sub, style: TextStyle(color: Colors.white.withOpacity(0.4), fontSize: 10)),
      ]),
    );
  }

  void _showNoDataDialog() {
    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF161B22),
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (_) => Padding(
        padding: const EdgeInsets.fromLTRB(22, 22, 22, 30),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text('Quality Report', style: TextStyle(color: Colors.white, fontSize: 17, fontWeight: FontWeight.w700)),
            const Divider(color: Colors.white12),
            const SizedBox(height: 16),
            const Row(children: [
              Icon(Icons.check_circle_outline, color: Color(0xFF50E3C2), size: 18),
              SizedBox(width: 8),
              Text('Audio decoded successfully', style: TextStyle(color: Color(0xFF50E3C2), fontSize: 13)),
            ]),
            const SizedBox(height: 10),
            Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Icon(Icons.info_outline, color: Colors.white.withOpacity(0.35), size: 16),
              const SizedBox(width: 8),
              Expanded(child: Text(
                'Quality metrics are being calculated.\nTry again in a moment.',
                style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 12, height: 1.4),
              )),
            ]),
            const SizedBox(height: 22),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () => Navigator.pop(context),
                style: ElevatedButton.styleFrom(backgroundColor: Colors.white10, padding: const EdgeInsets.symmetric(vertical: 14)),
                child: const Text('Close', style: TextStyle(color: Colors.white70)),
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0C10),
      appBar: AppBar(
        title: const Text('Result', style: TextStyle(color: Colors.white, letterSpacing: 2)),
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 8),
            child: _isSaving
                ? const Padding(
                    padding: EdgeInsets.all(14),
                    child: SizedBox(width: 20, height: 20,
                        child: CircularProgressIndicator(color: Color(0xFF50E3C2), strokeWidth: 2)),
                  )
                : IconButton(
                    onPressed: _saveImage,
                    tooltip: 'Save to Gallery',
                    icon: Container(
                      width: 36, height: 36,
                      decoration: BoxDecoration(
                        color: const Color(0xFF50E3C2).withOpacity(0.15),
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(color: const Color(0xFF50E3C2).withOpacity(0.4), width: 1.2),
                      ),
                      child: const Icon(Icons.save_alt_rounded, color: Color(0xFF50E3C2), size: 18),
                    ),
                  ),
          ),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(children: [
          Expanded(
            child: Center(
              child: InteractiveViewer(
                panEnabled: true,
                boundaryMargin: const EdgeInsets.all(20),
                minScale: 0.5, maxScale: 4,
                child: Image.memory(widget.imageBytes),
              ),
            ),
          ),
          const SizedBox(height: 16),
          SizedBox(
            width: double.infinity, height: 48,
            child: ElevatedButton(
              onPressed: _isLoadingReport ? null : _fetchReport,
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF50E3C2),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                elevation: 0,
              ),
              child: _isLoadingReport
                  ? const SizedBox(width: 22, height: 22, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                  : const Text('Show Report', style: TextStyle(fontSize: 15, color: Colors.black)),
            ),
          ),
        ]),
      ),
    );
  }
}