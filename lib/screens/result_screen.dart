import 'package:flutter/material.dart';
import '../models/prediction_response.dart';
import '../services/localization.dart';
// import '../main.dart'; // for localeNotifier

class ResultScreen extends StatefulWidget {
  final Map<String, dynamic>? optimizeResult;
  final PredictionResponse? prediction;
  final bool isQuintal;

  const ResultScreen({
    super.key,
    this.optimizeResult,
    this.prediction,
    this.isQuintal = true,
  });

  @override
  State<ResultScreen> createState() => _ResultScreenState();
}

class _ResultScreenState extends State<ResultScreen> {
  late bool _isQuintal;

  @override
  void initState() {
    super.initState();
    _isQuintal = widget.isQuintal;
  }

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<String>(
      valueListenable: localeNotifier,
      builder: (context, locale, child) {
        // If optimizeResult exists, show optimization UI.
        if (widget.optimizeResult != null) {
          return _buildOptimizationUI(context, locale);
        }
        // If prediction exists, show Standard UI (Forecast).
        if (widget.prediction != null) {
          return _buildStandardUI(context, locale);
        }

        return Scaffold(
          appBar: AppBar(
            title: Text(AppLocalizations.get(locale, 'results')),
            backgroundColor: Colors.green,
          ),
          body: const Center(child: Text("No data available.")),
        );
      },
    );
  }

  Widget _buildStandardUI(BuildContext context, String locale) {
    String unit = _isQuintal ? "Quintal" : "kg";
    double factor = _isQuintal ? 1.0 : 100.0;

    final predictions = widget.prediction!.predictions;
    double currentPrice = 0.0;
    double futurePrice = 0.0;
    if (predictions.isNotEmpty) {
      currentPrice = predictions.first.predictedPrice / factor;
      futurePrice = predictions.last.predictedPrice / factor;
    }
    double priceChange = futurePrice - currentPrice;

    // Evaluate raw change per quintal to apply the 50 Rs threshold
    double rawCurrent =
        predictions.isNotEmpty ? predictions.first.predictedPrice : 0.0;
    double rawFuture =
        predictions.isNotEmpty ? predictions.last.predictedPrice : 0.0;
    double rawChange = rawFuture - rawCurrent;

    String arrow = "➡";
    String trendText = "Stable Market";
    String message = "Prices are expected to remain stable.";
    Color trendColor = Colors.grey;

    if (rawChange > 50) {
      arrow = "⬆";
      trendText = "Rising Market";
      message = "Prices are expected to rise. Farmers can wait before selling.";
      trendColor = Colors.green;
    } else if (rawChange < -50) {
      arrow = "⬇";
      trendText = "Falling Market";
      message =
          "Prices are expected to fall. Selling soon may give a better price.";
      trendColor = Colors.red;
    }

    String changeText = priceChange == 0
        ? "No change expected"
        : "₹${priceChange.abs().toStringAsFixed(0)} ${priceChange > 0 ? "increase" : "decrease"} in next 7 days";

    return Scaffold(
      appBar: AppBar(
        title: Text(
          '${widget.prediction!.mandi} - ${widget.prediction!.commodity}',
        ),
        backgroundColor: const Color(0xFF1B5E20), // Dark Green
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
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Farmer Advisory Card
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.grey.shade300),
                boxShadow: [
                  BoxShadow(
                    color: Colors.grey.withValues(alpha: 0.1),
                    blurRadius: 4,
                    offset: const Offset(0, 2),
                  )
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Farmer Advisory',
                      style:
                          TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 16),
                  const Text('Current Price',
                      style: TextStyle(color: Colors.grey, fontSize: 13)),
                  const SizedBox(height: 2),
                  Text('₹${currentPrice.toStringAsFixed(0)} / $unit',
                      style: const TextStyle(
                          fontSize: 18, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 16),
                  const Text('Market Trend',
                      style: TextStyle(color: Colors.grey, fontSize: 13)),
                  const SizedBox(height: 2),
                  Row(
                    children: [
                      Text(arrow,
                          style: TextStyle(fontSize: 22, color: trendColor)),
                      const SizedBox(width: 8),
                      Text(trendText,
                          style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                              color: trendColor)),
                    ],
                  ),
                  const SizedBox(height: 16),
                  const Text('Expected Change',
                      style: TextStyle(color: Colors.grey, fontSize: 13)),
                  const SizedBox(height: 2),
                  Text(changeText,
                      style: const TextStyle(
                          fontSize: 15, fontWeight: FontWeight.w600)),
                  const SizedBox(height: 16),
                  const Text('Recommendation',
                      style: TextStyle(color: Colors.grey, fontSize: 13)),
                  const SizedBox(height: 2),
                  Text(message,
                      style: const TextStyle(
                          fontSize: 15, fontWeight: FontWeight.w500)),
                ],
              ),
            ),
            const SizedBox(height: 20),

            Text(
              AppLocalizations.get(locale, 'details'),
              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
            ),
            const SizedBox(height: 10),
            ListView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: widget.prediction!.predictions.length,
              itemBuilder: (ctx, i) {
                final p = widget.prediction!.predictions[i];
                double price = p.predictedPrice / factor;
                return Card(
                  child: ListTile(
                    leading: CircleAvatar(
                      backgroundColor: const Color(0xFFC8E6C9),
                      foregroundColor: const Color(0xFF1B5E20),
                      child: Text("${i + 1}d"),
                    ),
                    title: Text(
                      "${AppLocalizations.get(locale, 'date')}: ${p.date.toString().substring(0, 10)}",
                    ),
                    trailing: Text(
                      "₹${price.toStringAsFixed(0)}",
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 16,
                      ),
                    ),
                  ),
                );
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildOptimizationUI(BuildContext context, String locale) {
    final bestAction = widget.optimizeResult!['best_action'];
    final alternatives = widget.optimizeResult!['alternatives'] as List;
    final recText = widget.optimizeResult!['recommendation_text'];
    String unit = _isQuintal ? "q" : "kg";
    double factor = _isQuintal ? 1.0 : 100.0;

    // Handle case where no profitable option found (bestAction might be null)
    if (bestAction == null) {
      return Scaffold(
        appBar: AppBar(
          title: Text(AppLocalizations.get(locale, 'best_profit_calc')),
          backgroundColor: const Color(0xFF1B5E20), // Dark Green
          foregroundColor: Colors.white,
        ),
        body: const Center(
          child: Text("No profitable options found within constraints."),
        ),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: Text(AppLocalizations.get(locale, 'best_profit_calc')),
        backgroundColor: const Color(0xFF1B5E20), // Dark Green
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
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 1. Hero Card: Best Action
            Card(
              color: Colors.green.shade50,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(15),
                side: const BorderSide(color: Colors.green, width: 2),
              ),
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(
                          Icons.verified,
                          color: Colors.green,
                          size: 30,
                        ),
                        const SizedBox(width: 8),
                        Text(
                          AppLocalizations.get(locale, 'rec_action'),
                          style: const TextStyle(
                            fontWeight: FontWeight.bold,
                            color: Colors.green,
                            fontSize: 16,
                          ),
                        ),
                      ],
                    ),
                    const Divider(),
                    const SizedBox(height: 10),
                    Text(
                      recText, // This comes from backend-generated string, might need backend localization or client logic. Keeping as is for now.
                      style: const TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                        color: Colors.black87,
                      ),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 10),
                    Text(
                      "${AppLocalizations.get(locale, 'net_profit')}: ₹${bestAction['net_profit']}",
                      style: TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.w900,
                        color: (bestAction['net_profit'] as num) < 0
                            ? Colors.red
                            : Colors.green,
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 20),

            // 2. Alternatives List
            Text(
              AppLocalizations.get(locale, 'details'),
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 10),
            ListView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: alternatives.length,
              itemBuilder: (ctx, i) {
                final item = alternatives[i];
                final isBest = i == 0;
                final price =
                    (item['predicted_price'] as num).toDouble() / factor;

                return Card(
                  elevation: isBest ? 4 : 1,
                  child: ListTile(
                    leading: CircleAvatar(
                      backgroundColor: isBest
                          ? ((item['net_profit'] as num) < 0
                              ? Colors.red
                              : Colors.green)
                          : Colors.grey.shade300,
                      child: Text(
                        "${item['day_offset']}d",
                        style: TextStyle(
                          color: isBest ? Colors.white : Colors.black,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                    title: Text(
                      "${AppLocalizations.get(locale, 'sell_recc')} ${item['date']} @ ₹${price.toStringAsFixed(2)}/$unit",
                    ),
                    subtitle: Text(
                      "${AppLocalizations.get(locale, 'revenue')}: ₹${item['revenue']} - ${AppLocalizations.get(locale, 'costs')}: ₹${item['costs']}",
                    ),
                    trailing: Text(
                      "₹${item['net_profit']}",
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        color: (item['net_profit'] as num) < 0
                            ? Colors.red
                            : (isBest ? Colors.green : Colors.black),
                        fontSize: 16,
                      ),
                    ),
                  ),
                );
              },
            ),
          ],
        ),
      ),
    );
  }
}
