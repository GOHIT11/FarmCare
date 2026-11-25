import 'package:flutter/material.dart';
import 'dashboard_screen.dart';
import 'chat_screen.dart';
import 'edit_profile_screen.dart';
import '../services/localization.dart';

class MainScreen extends StatefulWidget {
  const MainScreen({super.key});

  @override
  State<MainScreen> createState() => _MainScreenState();
}

class _MainScreenState extends State<MainScreen> {
  int _currentIndex = 0;

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<String>(
      valueListenable: localeNotifier,
      builder: (context, locale, child) {
        final List<Widget> screens = [
          const DashboardScreen(), // Home
          PlaceholderWidget(
              title: AppLocalizations.get(
                  locale, 'all_farms')), // Placeholder for "All Farms"
          PlaceholderWidget(
              title: AppLocalizations.get(
                  locale, 'statistics')), // Placeholder for "Statistics/Trends"
          const EditProfileScreen(), // My Profile
        ];

        return Scaffold(
          body: IndexedStack(index: _currentIndex, children: screens),
          bottomNavigationBar: Container(
            decoration: BoxDecoration(
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withValues(alpha: 0.05),
                  blurRadius: 10,
                  offset: const Offset(0, -5),
                ),
              ],
            ),
            child: BottomNavigationBar(
              currentIndex: _currentIndex,
              onTap: (index) => setState(() => _currentIndex = index),
              type: BottomNavigationBarType.fixed,
              backgroundColor: Colors.white,
              selectedItemColor: const Color(0xFF1B5E20), // Deep Green
              unselectedItemColor: Colors.grey,
              showUnselectedLabels: true,
              selectedLabelStyle: const TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 12,
              ),
              unselectedLabelStyle: const TextStyle(
                fontWeight: FontWeight.normal,
                fontSize: 12,
              ),
              items: [
                BottomNavigationBarItem(
                  icon: const Icon(Icons.home_outlined),
                  activeIcon: const Icon(Icons.home),
                  label: AppLocalizations.get(locale, 'dashboard'),
                ),
                BottomNavigationBarItem(
                  icon: const Icon(Icons.agriculture_outlined),
                  activeIcon: const Icon(Icons.agriculture),
                  label: AppLocalizations.get(locale, 'my_farms'),
                ),
                BottomNavigationBarItem(
                  icon: const Icon(Icons.bar_chart_outlined),
                  activeIcon: const Icon(Icons.bar_chart),
                  label: AppLocalizations.get(locale, 'statistics'),
                ),
                BottomNavigationBarItem(
                  icon: const Icon(Icons.person_outline),
                  activeIcon: const Icon(Icons.person),
                  label: AppLocalizations.get(locale, 'my_profile'),
                ),
              ],
            ),
          ),
          floatingActionButton: _currentIndex == 0
              ? FloatingActionButton(
                  onPressed: () => Navigator.push(
                    context,
                    MaterialPageRoute(builder: (_) => const ChatScreen()),
                  ),
                  backgroundColor: const Color(0xFF1B5E20),
                  child: const Icon(Icons.chat_bubble_outline,
                      color: Colors.white),
                )
              : null,
        );
      },
    );
  }
}

// Temporary placeholder until we implement other tabs
class PlaceholderWidget extends StatelessWidget {
  final String title;
  const PlaceholderWidget({super.key, required this.title});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(title, style: const TextStyle(color: Color(0xFF1B5E20))),
        backgroundColor: Colors.transparent,
        elevation: 0,
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.construction, size: 60, color: Colors.grey[300]),
            const SizedBox(height: 16),
            Text(
              "$title Coming Soon",
              style: TextStyle(fontSize: 18, color: Colors.grey[600]),
            ),
          ],
        ),
      ),
    );
  }
}
