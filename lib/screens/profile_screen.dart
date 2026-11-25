import 'package:flutter/material.dart';
import '../services/auth_service.dart';
import 'edit_profile_screen.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final user = AuthService.currentUser;
    final name = user?['name'] ?? 'Guest';
    final district = user?['district'] ?? '';
    final mandiRaw = user?['mandi'] ?? '';
    // Mandis can be comma-separated (multi-mandi) or single
    final List<String> mandis = mandiRaw is String
        ? mandiRaw.split(',').where((m) => m.trim().isNotEmpty).toList()
        : [mandiRaw.toString()];
    final crops = List<String>.from(user?['crops'] ?? []);

    return Scaffold(
      appBar: AppBar(
        title: const Text("My Profile"),
        backgroundColor: const Color(0xFF1B5E20),
        foregroundColor: Colors.white,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            // Profile Header Card
            Card(
              elevation: 4,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(20),
              ),
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  children: [
                    const CircleAvatar(
                      radius: 50,
                      backgroundColor: Color(0xFFE8F5E9),
                      child: Icon(
                        Icons.person,
                        size: 60,
                        color: Color(0xFF1B5E20),
                      ),
                    ),
                    const SizedBox(height: 16),
                    Text(
                      name,
                      style: const TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                        color: Color(0xFF1B5E20),
                      ),
                    ),
                    const SizedBox(height: 8),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(Icons.location_on,
                            size: 16, color: Colors.grey),
                        const SizedBox(width: 4),
                        Text(
                          district.isNotEmpty
                              ? "$district, Andhra Pradesh"
                              : "Andhra Pradesh",
                          style:
                              const TextStyle(fontSize: 16, color: Colors.grey),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),

            // Registered Mandis Section
            _buildSection(
              context,
              title: "Registered Mandis",
              icon: Icons.store,
              items: mandis,
              chipColor: const Color(0xFFE3F2FD),
              chipTextColor: const Color(0xFF1565C0),
              chipIcon: Icons.store,
            ),
            const SizedBox(height: 16),

            // Registered Crops Section
            _buildSection(
              context,
              title: "Registered Crops",
              icon: Icons.eco,
              items: crops,
              chipColor: const Color(0xFFE8F5E9),
              chipTextColor: const Color(0xFF1B5E20),
              chipIcon: Icons.eco,
              showEditButton: true,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSection(
    BuildContext context, {
    required String title,
    required IconData icon,
    required List<String> items,
    required Color chipColor,
    required Color chipTextColor,
    required IconData chipIcon,
    bool showEditButton = false,
  }) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: Colors.grey.withValues(alpha: 0.1),
            blurRadius: 10,
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                title,
                style: const TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
              if (showEditButton)
                IconButton(
                  icon: const Icon(Icons.edit, color: Color(0xFF1B5E20)),
                  onPressed: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (_) => const EditProfileScreen(),
                      ),
                    );
                  },
                ),
            ],
          ),
          const Divider(),
          const SizedBox(height: 10),
          if (items.isEmpty)
            Text(
              "None selected",
              style: TextStyle(
                  color: Colors.grey[500], fontStyle: FontStyle.italic),
            )
          else
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: items
                  .map(
                    (item) => Chip(
                      label: Text(item),
                      backgroundColor: chipColor,
                      labelStyle: TextStyle(color: chipTextColor),
                      avatar: Icon(chipIcon, size: 16, color: chipTextColor),
                    ),
                  )
                  .toList(),
            ),
        ],
      ),
    );
  }
}
