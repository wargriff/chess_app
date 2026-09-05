import 'package:flutter/material.dart';
import 'package:chess_pro_d4/theme/catalog.dart';

/// Identité Chess Pro D4 — sombre, or discret (palette Pygame).
class D4Theme {
  static const Color bg = Color(0xFF080605);
  static const Color surface = Color(0xFF12100E);
  static const Color surfaceSoft = Color(0xFF1A1612);
  static const Color line = Color(0xFF3A342C);
  static const Color gold = Color(0xFFD4A548);
  static const Color goldBright = Color(0xFFE6BE64);
  static const Color goldDim = Color(0xFF785A28);
  static const Color text = Color(0xFFEBE1CD);
  static const Color muted = Color(0xFF8C7D6C);
  static const Color online = Color(0xFF50BE6E);
  static const Color offline = Color(0xFFC85046);
  static const Color lightSq = Color(0xFFA89476);
  static const Color darkSq = Color(0xFF4E3A2A);

  static ThemeData fromAppTheme(AppThemeInfo t) {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      scaffoldBackgroundColor: t.bg,
      colorScheme: ColorScheme.dark(
        primary: t.gold,
        secondary: goldBright,
        surface: t.surface,
        onPrimary: Colors.black,
        onSurface: text,
      ),
      dividerColor: line,
      appBarTheme: AppBarTheme(
        backgroundColor: t.surface,
        foregroundColor: text,
        elevation: 0,
        centerTitle: false,
      ),
      tabBarTheme: TabBarThemeData(
        labelColor: goldBright,
        unselectedLabelColor: muted,
        indicatorColor: t.gold,
        dividerColor: Colors.transparent,
        tabAlignment: TabAlignment.start,
      ),
      cardTheme: CardThemeData(
        color: t.surface,
        elevation: 0,
        margin: EdgeInsets.zero,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(10),
          side: const BorderSide(color: line),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: surfaceSoft,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: line),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: line),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: BorderSide(color: t.gold),
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: t.gold,
          foregroundColor: Colors.black,
          padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: text,
          side: const BorderSide(color: line),
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
        ),
      ),
      chipTheme: ChipThemeData(
        backgroundColor: t.bg,
        selectedColor: surfaceSoft,
        side: const BorderSide(color: line),
        labelStyle: const TextStyle(color: muted, fontSize: 13),
      ),
      sliderTheme: SliderThemeData(
        activeTrackColor: t.gold,
        thumbColor: goldBright,
        inactiveTrackColor: line,
      ),
    );
  }

  static ThemeData dark() => fromAppTheme(appThemes.first);
}
