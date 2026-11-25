import 'package:flutter/material.dart';
import '../services/auth_service.dart';
import '../services/api_service.dart';
import '../services/localization.dart';
import '../services/data_localization.dart';
import 'dashboard_screen.dart';

class EditProfileScreen extends StatefulWidget {
  const EditProfileScreen({super.key});

  @override
  State<EditProfileScreen> createState() => _EditProfileScreenState();
}

class _EditProfileScreenState extends State<EditProfileScreen> {
  final _apiService = MandiApiService();
  final _authService = AuthService();

  Map<String, dynamic> _masterData = {};
  Map<String, dynamic> _districtMandis = {};
  List<String> _districts = [];
  List<String> _mandis = [];

  // Multi-mandi selection
  final List<String> _selectedMandis = [];
  List<String> _availableCrops = [];
  List<String> _selectedCrops = [];
  String? _selectedDistrict;
  bool _isLoading = false;
  bool _dataLoaded = false;

  @override
  void initState() {
    super.initState();
    _loadOptionsAndUser();
  }

  Future<void> _loadOptionsAndUser() async {
    final data = await _apiService.fetchOptions();
    final districts = await _apiService.fetchDistricts();
    final user = AuthService.currentUser;

    setState(() {
      _masterData = data['Andhra Pradesh'] ?? data;
      _districtMandis = districts;
      // Deduplicate districts
      _districts = _districtMandis.keys.toSet().toList()..sort();

      if (user != null) {
        final savedDistrict = (user['district'] ?? '').toString().trim();
        // Only set if the district actually exists in the list
        if (savedDistrict.isNotEmpty && _districts.contains(savedDistrict)) {
          _selectedDistrict = savedDistrict;
        } else {
          _selectedDistrict = null;
        }

        // Load Mandis for this district
        if (_selectedDistrict != null &&
            _districtMandis.containsKey(_selectedDistrict)) {
          final mandisList = _districtMandis[_selectedDistrict] as List? ?? [];
          _mandis = mandisList.cast<String>().toSet().toList()..sort();
        }

        // Load selected mandis (comma-separated)
        final mandiRaw = user['mandi'] ?? '';
        if (mandiRaw is String && mandiRaw.isNotEmpty) {
          _selectedMandis.addAll(
            mandiRaw
                .split(',')
                .where((m) => m.trim().isNotEmpty)
                .map((m) => m.trim()),
          );
        }

        // Aggregate available crops from selected mandis
        _updateAvailableCrops();

        // Load selected crops
        _selectedCrops = List<String>.from(user['crops'] ?? []);
      }
      _dataLoaded = true;
    });
  }

  void _updateAvailableCrops() {
    final Set<String> allCrops = {};
    for (final m in _selectedMandis) {
      if (_masterData.containsKey(m)) {
        final rawCrops = _masterData[m] as List;
        allCrops.addAll(rawCrops.cast<String>());
      }
    }
    _availableCrops = allCrops.toList()..sort();
    // Remove any selected crops that are no longer available
    _selectedCrops.removeWhere((c) => !_availableCrops.contains(c));
  }

  void _onDistrictChanged(String? val) {
    if (val == null) return;
    setState(() {
      _selectedDistrict = val;
      final mandisList = _districtMandis[val] as List? ?? [];
      _mandis = mandisList.cast<String>().toSet().toList()..sort();
      _selectedMandis.clear();
      _availableCrops = [];
      _selectedCrops.clear();
    });
  }

  void _onMandiToggled(String mandi, bool selected) {
    setState(() {
      if (selected) {
        _selectedMandis.add(mandi);
      } else {
        _selectedMandis.remove(mandi);
      }
      _updateAvailableCrops();
    });
  }

  void _saveProfile() async {
    final user = AuthService.currentUser;
    if (user == null) return;

    if (_selectedDistrict == null ||
        _selectedMandis.isEmpty ||
        _selectedCrops.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text("Please select district, mandis, and crops"),
        ),
      );
      return;
    }

    setState(() => _isLoading = true);
    final success = await _authService.updateProfile(
      name: user['name'],
      state: "Andhra Pradesh",
      district: _selectedDistrict!,
      mandi: _selectedMandis.join(","), // Store as comma-separated
      crops: _selectedCrops,
    );
    setState(() => _isLoading = false);

    if (success && mounted) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(
          content: Text(
              AppLocalizations.get(localeNotifier.value, 'profile_updated'))));
      Navigator.pushAndRemoveUntil(
        context,
        MaterialPageRoute(builder: (_) => const DashboardScreen()),
        (route) => false,
      );
    } else if (mounted) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(
          content: Text(
              AppLocalizations.get(localeNotifier.value, 'update_failed'))));
    }
  }

  @override
  Widget build(BuildContext context) {
    // Don't render dropdowns until data is loaded
    if (!_dataLoaded) {
      return Scaffold(
        appBar: AppBar(
          title: Text(AppLocalizations.get(localeNotifier.value, 'profile')),
          backgroundColor: const Color(0xFF1B5E20),
          foregroundColor: Colors.white,
        ),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    return ValueListenableBuilder<String>(
      valueListenable: localeNotifier,
      builder: (context, locale, child) {
        // Ensure _selectedDistrict is valid RIGHT before rendering
        final safeDistrict = (_selectedDistrict != null &&
                _selectedDistrict!.isNotEmpty &&
                _districts.contains(_selectedDistrict))
            ? _selectedDistrict
            : null;

        return Scaffold(
          appBar: AppBar(
            title: Text(AppLocalizations.get(locale, 'profile')),
            backgroundColor: const Color(0xFF1B5E20),
            foregroundColor: Colors.white,
          ),
          body: SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // AP Badge
                Center(
                  child: Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 10,
                      vertical: 4,
                    ),
                    decoration: BoxDecoration(
                      color: const Color(0xFFE8F5E9),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Text(
                      "🌾 Andhra Pradesh",
                      style: TextStyle(
                        color: Color(0xFF1B5E20),
                        fontSize: 12,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 4),
                Center(
                  child: Text(
                    AppLocalizations.get(locale, 'update_profile_desc'),
                    style: TextStyle(fontSize: 13, color: Colors.grey[600]),
                  ),
                ),
                const SizedBox(height: 12),

                // District Dropdown — key forces rebuild when data changes
                if (_districts.isNotEmpty)
                  DropdownButtonFormField<String>(
                    initialValue: safeDistrict,
                    decoration: InputDecoration(
                      labelText: AppLocalizations.get(
                        locale,
                        'select_district',
                      ),
                      border: const OutlineInputBorder(),
                    ),
                    hint: Text(AppLocalizations.get(locale, 'select_district')),
                    onChanged: _onDistrictChanged,
                    items: _districts
                        .where((d) => d.trim().isNotEmpty)
                        .toSet()
                        .toList()
                        .map(
                          (d) => DropdownMenuItem(
                            value: d,
                            child: Text(DataLocalization.get(d, locale)),
                          ),
                        )
                        .toList(),
                  ),
                const SizedBox(height: 20),

                // Multi-Mandi Selection
                if (safeDistrict != null && _mandis.isNotEmpty) ...[
                  Text(
                    AppLocalizations.get(locale, 'select_your_mandis'),
                    style: const TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 16,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    AppLocalizations.get(locale, 'select_all_mandis'),
                    style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                  ),
                  const SizedBox(height: 10),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: _mandis.map((mandi) {
                      final isSelected = _selectedMandis.contains(mandi);
                      return FilterChip(
                        label: Text(DataLocalization.get(mandi, locale)),
                        selected: isSelected,
                        selectedColor: const Color(0xFFC8E6C9),
                        checkmarkColor: const Color(0xFF1B5E20),
                        avatar: Icon(
                          Icons.store,
                          size: 16,
                          color: isSelected
                              ? const Color(0xFF1B5E20)
                              : Colors.grey,
                        ),
                        onSelected: (selected) =>
                            _onMandiToggled(mandi, selected),
                      );
                    }).toList(),
                  ),
                ],

                // Crop Selection
                if (_selectedMandis.isNotEmpty &&
                    _availableCrops.isNotEmpty) ...[
                  const SizedBox(height: 24),
                  Text(
                    AppLocalizations.get(locale, 'select_crops'),
                    style: const TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 16,
                    ),
                  ),
                  const SizedBox(height: 10),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: _availableCrops.map((crop) {
                      final isSelected = _selectedCrops.contains(crop);
                      return FilterChip(
                        label: Text(DataLocalization.get(crop, locale)),
                        selected: isSelected,
                        selectedColor: const Color(0xFFE8F5E9),
                        checkmarkColor: const Color(0xFF1B5E20),
                        onSelected: (selected) {
                          setState(() {
                            if (selected) {
                              _selectedCrops.add(crop);
                            } else {
                              _selectedCrops.remove(crop);
                            }
                          });
                        },
                      );
                    }).toList(),
                  ),
                ],

                const SizedBox(height: 30),
                SizedBox(
                  width: double.infinity,
                  height: 56,
                  child: ElevatedButton(
                    onPressed: _isLoading ? null : _saveProfile,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF1B5E20),
                      foregroundColor: Colors.white,
                      textStyle: const TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    child: _isLoading
                        ? const CircularProgressIndicator(color: Colors.white)
                        : Text(
                            AppLocalizations.get(locale, 'save').toUpperCase(),
                          ),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}
