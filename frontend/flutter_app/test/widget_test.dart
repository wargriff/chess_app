import 'package:flutter_test/flutter_test.dart';
import 'package:chess_pro_d4/theme/d4_theme.dart';
import 'package:flutter/material.dart';

void main() {
  testWidgets('D4 theme builds MaterialApp', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        theme: D4Theme.dark(),
        home: const Scaffold(body: Text('Chess Pro D4')),
      ),
    );
    expect(find.text('Chess Pro D4'), findsOneWidget);
  });
}
