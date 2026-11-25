import 'package:flutter/material.dart';
import '../services/auth_service.dart';
import '../services/api_service.dart';
import '../services/localization.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _nameController = TextEditingController();
  final _passController = TextEditingController();

  final _apiService = MandiApiService();
  final _authService = AuthService();

  Map<String, dynamic> _masterData = {};
  Map<String, dynamic> _districtMandis = {};
  List<String> _districts = [];
  List<String> _mandis = [];

  // Multi-mandi selection
  final List<String> _selectedMandis = [];
  // Crops aggregated from all selected mandis
  List<String> _availableCrops = [];
  final List<String> _selectedCrops = [];

  String? _selectedDistrict;

  bool _isLoading = false;
  bool _isPasswordVisible = false;

  @override
  void initState() {
    super.initState();
    _loadOptions();
  }

  Future<void> _loadOptions() async {
    try {
      final data = await _apiService.fetchOptions();
      final districts = await _apiService.fetchDistricts();
      setState(() {
        _masterData = data['Andhra Pradesh'] ?? data;
        _districtMandis = districts;
        _districts = _districtMandis.keys.toList()..sort();
      });
    } catch (e) {
      // Handle error
    }
  }

  void _onDistrictChanged(String? val) {
    setState(() {
      _selectedDistrict = val;
      final mandisList = _districtMandis[val!] as List? ?? [];
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
      // Aggregate crops from ALL selected mandis
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
    });
  }

  void _register() async {
    if (_nameController.text.isEmpty ||
        _passController.text.isEmpty ||
        _selectedDistrict == null ||
        _selectedMandis.isEmpty ||
        _selectedCrops.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
            content: Text(
                "Please fill all fields and select at least one mandi and crop")),
      );
      return;
    }

    setState(() => _isLoading = true);
    final success = await _authService.register(
      name: _nameController.text,
      password: _passController.text,
      state: "Andhra Pradesh",
      district: _selectedDistrict!,
      mandi: _selectedMandis.join(","), // Store as comma-separated
      crops: _selectedCrops,
    );
    setState(() => _isLoading = false);

    if (success && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Registration Successful! Please Login.")),
      );
      Navigator.pop(context);
    } else if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Registration Failed")),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.white),
        title: const Text(
          "Create Account",
          style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
        ),
      ),
      body: Stack(
        children: [
          Positioned(
            top: 0,
            left: 0,
            right: 0,
            height: 250,
            child: Container(
              decoration: const BoxDecoration(
                gradient: LinearGradient(
                  colors: [Color(0xFF1B5E20), Color(0xFF43A047)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.only(
                  bottomLeft: Radius.circular(60),
                  bottomRight: Radius.circular(60),
                ),
              ),
            ),
          ),
          SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(20),
              child: Column(
                children: [
                  const SizedBox(height: 20),
                  Container(
                    padding: const EdgeInsets.all(24),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(24),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withValues(alpha: 0.1),
                          blurRadius: 20,
                          offset: const Offset(0, 10),
                        ),
                      ],
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Center(
                          child: Text(
                            AppLocalizations.get(
                                localeNotifier.value, 'join_mandi'),
                            style: const TextStyle(
                              fontSize: 22,
                              fontWeight: FontWeight.bold,
                              color: Color(0xFF1B5E20),
                            ),
                          ),
                        ),
                        const SizedBox(height: 8),
                        Center(
                          child: Container(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 10, vertical: 4),
                            decoration: BoxDecoration(
                              color: const Color(0xFFE8F5E9),
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: Text(
                              AppLocalizations.get(
                                  localeNotifier.value, 'for_ap_farmers'),
                              style: const TextStyle(
                                color: Color(0xFF1B5E20),
                                fontSize: 12,
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(height: 24),

                        // Name
                        TextField(
                          controller: _nameController,
                          decoration: InputDecoration(
                            labelText: AppLocalizations.get(
                                localeNotifier.value, 'full_name'),
                            prefixIcon: const Icon(Icons.person),
                          ),
                        ),
                        const SizedBox(height: 16),
                        // Password
                        TextField(
                          controller: _passController,
                          obscureText: !_isPasswordVisible,
                          decoration: InputDecoration(
                            labelText: AppLocalizations.get(
                                localeNotifier.value, 'password'),
                            prefixIcon: const Icon(Icons.lock),
                            suffixIcon: IconButton(
                              icon: Icon(
                                _isPasswordVisible
                                    ? Icons.visibility
                                    : Icons.visibility_off,
                              ),
                              onPressed: () {
                                setState(() =>
                                    _isPasswordVisible = !_isPasswordVisible);
                              },
                            ),
                          ),
                        ),
                        const SizedBox(height: 16),
                        // District Dropdown
                        DropdownButtonFormField<String>(
                          initialValue: _selectedDistrict,
                          decoration: const InputDecoration(
                            labelText: "Select District",
                            prefixIcon: Icon(Icons.map),
                          ),
                          onChanged: _onDistrictChanged,
                          items: _districts
                              .map((d) =>
                                  DropdownMenuItem(value: d, child: Text(d)))
                              .toList(),
                        ),
                        const SizedBox(height: 20),

                        // Multi-Mandi Selection (Chips)
                        if (_selectedDistrict != null &&
                            _mandis.isNotEmpty) ...[
                          const Text(
                            "Select Your Mandis:",
                            style: TextStyle(
                                fontWeight: FontWeight.bold, fontSize: 16),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            "Select all mandis where you sell your crops",
                            style: TextStyle(
                                fontSize: 12, color: Colors.grey[600]),
                          ),
                          const SizedBox(height: 10),
                          Wrap(
                            spacing: 8,
                            runSpacing: 8,
                            children: _mandis.map((mandi) {
                              final isSelected =
                                  _selectedMandis.contains(mandi);
                              return FilterChip(
                                label: Text(mandi),
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
                                labelStyle: TextStyle(
                                  color: isSelected
                                      ? const Color(0xFF1B5E20)
                                      : Colors.black87,
                                  fontWeight: isSelected
                                      ? FontWeight.bold
                                      : FontWeight.normal,
                                ),
                                onSelected: (selected) =>
                                    _onMandiToggled(mandi, selected),
                              );
                            }).toList(),
                          ),
                        ],

                        // Crop Selection (only after mandis are selected)
                        if (_selectedMandis.isNotEmpty &&
                            _availableCrops.isNotEmpty) ...[
                          const SizedBox(height: 24),
                          const Text(
                            "Select Your Crops:",
                            style: TextStyle(
                                fontWeight: FontWeight.bold, fontSize: 16),
                          ),
                          const SizedBox(height: 10),
                          Wrap(
                            spacing: 8,
                            runSpacing: 8,
                            children: _availableCrops.map((crop) {
                              final isSelected = _selectedCrops.contains(crop);
                              return FilterChip(
                                label: Text(crop),
                                selected: isSelected,
                                selectedColor: const Color(0xFFE8F5E9),
                                checkmarkColor: const Color(0xFF1B5E20),
                                labelStyle: TextStyle(
                                  color: isSelected
                                      ? const Color(0xFF1B5E20)
                                      : Colors.black87,
                                  fontWeight: isSelected
                                      ? FontWeight.bold
                                      : FontWeight.normal,
                                ),
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
                            onPressed: _isLoading ? null : _register,
                            child: _isLoading
                                ? const SizedBox(
                                    height: 24,
                                    width: 24,
                                    child: CircularProgressIndicator(
                                      color: Colors.white,
                                      strokeWidth: 2,
                                    ),
                                  )
                                : const Text("REGISTER NOW"),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
