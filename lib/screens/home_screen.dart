import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/localization.dart';
import '../services/data_localization.dart';
import 'result_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final MandiApiService _apiService = MandiApiService();

  // Master Data: {Mandi: [Commodities]} under "Andhra Pradesh"
  Map<String, dynamic> _masterData = {};
  // District -> Mandi mapping
  Map<String, dynamic> _districtMandis = {};

  List<String> _districts = [];
  List<String> _mandis = [];
  List<String> _commodities = [];

  String? _selectedDistrict;
  String? _selectedMandi;
  String? _selectedCommodity;

  final TextEditingController _qtyController = TextEditingController();
  final TextEditingController _storageController = TextEditingController();
  final TextEditingController _storageCostController = TextEditingController();
  final TextEditingController _transportCostController =
      TextEditingController();
  final TextEditingController _distController = TextEditingController();

  bool _isLoadingOptions = true;
  String? _error;
  bool _isQuintal = true;

  @override
  void initState() {
    super.initState();
    _loadOptions();
  }

  Future<void> _loadOptions() async {
    setState(() {
      _isLoadingOptions = true;
      _error = null;
    });

    try {
      final options = await _apiService.fetchOptions();
      final districts = await _apiService.fetchDistricts();

      setState(() {
        _masterData = options['Andhra Pradesh'] ?? options;
        _districtMandis = districts;
        _districts = _districtMandis.keys.toList();
        _districts.sort();

        if (_districts.isNotEmpty) {
          _selectedDistrict = _districts[0];
          _updateMandis();
        }

        _isLoadingOptions = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoadingOptions = false;
      });
    }
  }

  void _updateMandis() {
    if (_selectedDistrict == null) return;
    final mandisList = _districtMandis[_selectedDistrict] as List? ?? [];
    _mandis = mandisList.cast<String>().toSet().toList();
    _mandis.sort();

    if (_mandis.isNotEmpty) {
      _selectedMandi = _mandis[0];
      _updateCommodities();
    } else {
      _selectedMandi = null;
      _commodities = [];
      _selectedCommodity = null;
    }
  }

  void _updateCommodities() {
    if (_selectedMandi == null) return;
    final commoditiesList = _masterData[_selectedMandi] as List? ?? [];
    _commodities = commoditiesList.cast<String>().toSet().toList();
    _commodities.sort();

    if (_commodities.isNotEmpty) {
      _selectedCommodity = _commodities[0];
    } else {
      _selectedCommodity = null;
    }
  }

  void _getForecast() async {
    if (_selectedMandi == null || _selectedCommodity == null) return;

    _showLoading();
    try {
      final prediction = await _apiService.fetchPrediction(
        mandi: _selectedMandi!,
        commodity: _selectedCommodity!,
      );
      if (!mounted) return;
      Navigator.pop(context);
      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (_) =>
              ResultScreen(prediction: prediction, isQuintal: _isQuintal),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      Navigator.pop(context);
      _showError(e.toString());
    }
  }

  void _getOptimizedPlan() async {
    if (_selectedMandi == null || _selectedCommodity == null) {
      _showError("Please select Mandi and Commodity");
      return;
    }

    if (_qtyController.text.isEmpty ||
        _storageController.text.isEmpty ||
        _transportCostController.text.isEmpty) {
      _showError(
        "Please fill in farmer profile details (Quantity, Storage, Costs) to calculate profit.",
      );
      return;
    }

    _showLoading();

    try {
      double qVal = double.tryParse(_qtyController.text) ?? 10;
      if (!_isQuintal) {
        qVal = qVal / 100.0;
      }
      final optimizeResult = await _apiService.optimizeProfile(
        mandis: [_selectedMandi!],
        commodity: _selectedCommodity!,
        quantityQuintal: qVal,
        storageDaysMax: int.tryParse(_storageController.text) ?? 3,
        storageCost: double.tryParse(_storageCostController.text) ?? 5,
        transportCost: double.tryParse(_transportCostController.text) ?? 5,
        distanceToMandi: {
          _selectedMandi!: double.tryParse(_distController.text) ?? 10,
        },
      );

      if (!mounted) return;
      Navigator.pop(context);

      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (context) => ResultScreen(
            optimizeResult: optimizeResult,
            isQuintal: _isQuintal,
          ),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      Navigator.pop(context);
      _showError(e.toString());
    }
  }

  void _showLoading() {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (_) => const Center(child: CircularProgressIndicator()),
    );
  }

  void _showError(String msg) {
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(SnackBar(content: Text(msg), backgroundColor: Colors.red));
  }

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<String>(
      valueListenable: localeNotifier,
      builder: (context, locale, child) {
        return Scaffold(
          appBar: AppBar(
            title: Text(AppLocalizations.get(locale, 'farmer_advisor')),
            backgroundColor: const Color(0xFF1B5E20),
            foregroundColor: Colors.white,
            actions: [
              Row(
                children: [
                  Text(
                    _isQuintal
                        ? AppLocalizations.get(locale, 'unit_q')
                        : AppLocalizations.get(locale, 'unit_kg'),
                    style: const TextStyle(fontWeight: FontWeight.bold),
                  ),
                  Switch(
                    value: _isQuintal,
                    activeThumbColor: Colors.white,
                    activeTrackColor: Colors.green.shade800,
                    onChanged: (val) {
                      setState(() {
                        _isQuintal = val;
                      });
                    },
                  ),
                ],
              ),
              const SizedBox(width: 8),
            ],
          ),
          body: _isLoadingOptions
              ? const Center(child: CircularProgressIndicator())
              : _error != null
                  ? Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Icon(
                            Icons.error_outline,
                            color: Colors.red,
                            size: 48,
                          ),
                          const SizedBox(height: 16),
                          Text(
                            'Connection Error',
                            style: Theme.of(context).textTheme.titleLarge,
                          ),
                          Padding(
                            padding: const EdgeInsets.all(16.0),
                            child: Text(
                              _error!,
                              textAlign: TextAlign.center,
                              style: const TextStyle(color: Colors.grey),
                            ),
                          ),
                        ],
                      ),
                    )
                  : SingleChildScrollView(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          // AP Badge
                          Container(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 12, vertical: 6),
                            decoration: BoxDecoration(
                              color: const Color(0xFFE8F5E9),
                              borderRadius: BorderRadius.circular(20),
                            ),
                            child: Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                const Icon(Icons.location_on,
                                    color: Color(0xFF1B5E20), size: 16),
                                const SizedBox(width: 4),
                                Text(
                                  "Andhra Pradesh",
                                  style: TextStyle(
                                    color: const Color(0xFF1B5E20),
                                    fontWeight: FontWeight.bold,
                                    fontSize: 13,
                                  ),
                                ),
                              ],
                            ),
                          ),
                          const SizedBox(height: 12),

                          // --- SELECTION CARD ---
                          Card(
                            elevation: 4,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(16),
                            ),
                            child: Padding(
                              padding: const EdgeInsets.all(16.0),
                              child: Column(
                                children: [
                                  // District Dropdown
                                  InputDecorator(
                                    decoration: InputDecoration(
                                      labelText: AppLocalizations.get(
                                        locale,
                                        'select_district',
                                      ),
                                      border: OutlineInputBorder(
                                        borderRadius: BorderRadius.circular(12),
                                      ),
                                      contentPadding:
                                          const EdgeInsets.symmetric(
                                        horizontal: 16,
                                        vertical: 12,
                                      ),
                                    ),
                                    child: DropdownButtonHideUnderline(
                                      child: DropdownButton<String>(
                                        value: _selectedDistrict,
                                        isDense: true,
                                        isExpanded: true,
                                        onChanged: (val) {
                                          setState(() {
                                            _selectedDistrict = val;
                                            _updateMandis();
                                          });
                                        },
                                        items: _districts.map((d) {
                                          return DropdownMenuItem(
                                            value: d,
                                            child: Text(
                                              DataLocalization.get(d, locale),
                                              style: const TextStyle(
                                                fontWeight: FontWeight.bold,
                                              ),
                                            ),
                                          );
                                        }).toList(),
                                      ),
                                    ),
                                  ),
                                  const SizedBox(height: 16),
                                  // Mandi Dropdown
                                  InputDecorator(
                                    decoration: InputDecoration(
                                      labelText: AppLocalizations.get(
                                        locale,
                                        'select_mandi',
                                      ),
                                      border: OutlineInputBorder(
                                        borderRadius: BorderRadius.circular(12),
                                      ),
                                      contentPadding:
                                          const EdgeInsets.symmetric(
                                        horizontal: 16,
                                        vertical: 12,
                                      ),
                                    ),
                                    child: DropdownButtonHideUnderline(
                                      child: DropdownButton<String>(
                                        value: _selectedMandi,
                                        isDense: true,
                                        isExpanded: true,
                                        onChanged: (val) {
                                          setState(() {
                                            _selectedMandi = val;
                                            _updateCommodities();
                                          });
                                        },
                                        items: _mandis.map((m) {
                                          return DropdownMenuItem(
                                            value: m,
                                            child: Text(
                                              DataLocalization.get(m, locale),
                                            ),
                                          );
                                        }).toList(),
                                      ),
                                    ),
                                  ),
                                  const SizedBox(height: 16),
                                  // Commodity Dropdown
                                  InputDecorator(
                                    decoration: InputDecoration(
                                      labelText: AppLocalizations.get(
                                        locale,
                                        'select_commodity',
                                      ),
                                      border: OutlineInputBorder(
                                        borderRadius: BorderRadius.circular(12),
                                      ),
                                      contentPadding:
                                          const EdgeInsets.symmetric(
                                        horizontal: 16,
                                        vertical: 12,
                                      ),
                                    ),
                                    child: DropdownButtonHideUnderline(
                                      child: DropdownButton<String>(
                                        value: _selectedCommodity,
                                        isDense: true,
                                        isExpanded: true,
                                        onChanged: (val) {
                                          setState(() {
                                            _selectedCommodity = val;
                                          });
                                        },
                                        items: _commodities.map((c) {
                                          return DropdownMenuItem(
                                            value: c,
                                            child: Text(
                                              DataLocalization.get(c, locale),
                                            ),
                                          );
                                        }).toList(),
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),
                          const SizedBox(height: 24),

                          // --- BUTTON: DAILY PRICE FORECAST ---
                          SizedBox(
                            width: double.infinity,
                            child: OutlinedButton.icon(
                              style: OutlinedButton.styleFrom(
                                foregroundColor: const Color(0xFF1B5E20),
                                side:
                                    const BorderSide(color: Color(0xFF1B5E20)),
                                padding:
                                    const EdgeInsets.symmetric(vertical: 16),
                                shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(30),
                                ),
                              ),
                              onPressed: _getForecast,
                              icon: const Icon(Icons.trending_up),
                              label: const Text(
                                "Get 7-Day Daily Forecast",
                                style: TextStyle(
                                  fontSize: 16,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ),
                          ),
                          const SizedBox(height: 24),
                          const Divider(),
                          const SizedBox(height: 16),

                          // --- OPTIMIZATION SECTION ---
                          Text(
                            AppLocalizations.get(locale, 'farmer_profile_opt'),
                            style: Theme.of(context)
                                .textTheme
                                .titleLarge
                                ?.copyWith(
                                  fontWeight: FontWeight.bold,
                                ),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            "Enter your farming and selling details below to calculate the best time to sell your crop and maximize profit.",
                            style: TextStyle(
                                color: Colors.grey[700], fontSize: 14),
                          ),
                          const SizedBox(height: 24),

                          _buildOptimizationField(
                            controller: _qtyController,
                            label: "Quantity to Sell (Quintals)",
                            hint: "Example: 10",
                            helper:
                                "Enter how much crop you want to sell in the market.",
                            icon: Icons.scale,
                          ),
                          const SizedBox(height: 16),

                          _buildOptimizationField(
                            controller: _storageController,
                            label: "Maximum Storage Days",
                            hint: "Example: 5",
                            helper:
                                "How many days can you store this crop before selling?",
                            icon: Icons.calendar_today,
                          ),
                          const SizedBox(height: 16),

                          _buildOptimizationField(
                            controller: _storageCostController,
                            label: "Storage Cost (₹ / day)",
                            hint: "Example: 50",
                            helper:
                                "Cost of storing the crop per day (cold storage or warehouse).",
                            icon: Icons.money,
                          ),
                          const SizedBox(height: 16),

                          _buildOptimizationField(
                            controller: _transportCostController,
                            label: "Transport Cost (₹)",
                            hint: "Example: 300",
                            helper:
                                "Total cost to transport the crop to the mandi.",
                            icon: Icons.local_shipping,
                          ),
                          const SizedBox(height: 16),

                          _buildOptimizationField(
                            controller: _distController,
                            label: "Distance to Mandi (km)",
                            hint: "Example: 15",
                            helper:
                                "Distance from your farm to the selected mandi.",
                            icon: Icons.map,
                          ),
                          const SizedBox(height: 24),

                          SizedBox(
                            width: double.infinity,
                            height: 55,
                            child: ElevatedButton.icon(
                              onPressed: _getOptimizedPlan,
                              style: ElevatedButton.styleFrom(
                                backgroundColor: const Color(0xFF1B5E20),
                                foregroundColor: Colors.white,
                                shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(30),
                                ),
                                elevation: 5,
                              ),
                              icon: const Icon(Icons.rocket_launch),
                              label: Text(
                                AppLocalizations.get(
                                    locale, 'calculate_profit'),
                                style: const TextStyle(
                                  fontSize: 18,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ),
                          ),
                          const SizedBox(height: 40),
                        ],
                      ),
                    ),
        );
      },
    );
  }

  Widget _buildOptimizationField({
    required TextEditingController controller,
    required String label,
    required String hint,
    required String helper,
    required IconData icon,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
        ),
        const SizedBox(height: 8),
        TextField(
          controller: controller,
          keyboardType: TextInputType.number,
          decoration: InputDecoration(
            hintText: hint,
            hintStyle: TextStyle(color: Colors.grey.shade400),
            prefixIcon: Icon(icon, color: Colors.green, size: 22),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(color: Colors.grey.shade300),
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(color: Colors.grey.shade300),
            ),
            filled: true,
            fillColor: Colors.white,
            contentPadding: const EdgeInsets.symmetric(vertical: 16),
          ),
        ),
        const SizedBox(height: 6),
        Text(
          helper,
          style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
        ),
      ],
    );
  }
}
