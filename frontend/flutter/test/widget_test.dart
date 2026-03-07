import 'package:flutter_test/flutter_test.dart';

import 'package:memscreen_flutter/main.dart';

void main() {
  testWidgets('MemScreen app smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const MemScreenApp());
    await tester.pump();

    expect(find.text('Record'), findsOneWidget);
    expect(find.text('Chat'), findsOneWidget);
  });
}
