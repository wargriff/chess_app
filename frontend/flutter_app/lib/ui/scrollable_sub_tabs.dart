import 'package:flutter/material.dart';

import 'package:chess_pro_d4/theme/d4_theme.dart';

/// Sous-onglets VERTICAUX défilables (liste à gauche).
class VerticalSubNav extends StatelessWidget {
  const VerticalSubNav({
    super.key,
    required this.labels,
    required this.index,
    required this.onChanged,
    this.icons,
    this.title,
    this.width = 200,
  });

  final List<String> labels;
  final List<IconData>? icons;
  final int index;
  final ValueChanged<int> onChanged;
  final String? title;
  final double width;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: D4Theme.surface,
      child: SizedBox(
        width: width,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            if (title != null)
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 16, 12, 8),
                child: Text(
                  title!,
                  style: const TextStyle(
                    color: D4Theme.goldBright,
                    fontWeight: FontWeight.w700,
                    fontSize: 15,
                    letterSpacing: 0.3,
                  ),
                ),
              ),
            Expanded(
              child: ListView.builder(
                physics: const BouncingScrollPhysics(),
                padding: const EdgeInsets.fromLTRB(8, 4, 8, 16),
                itemCount: labels.length,
                itemBuilder: (context, i) {
                  final selected = i == index;
                  final icon = icons != null && i < icons!.length ? icons![i] : null;
                  return Padding(
                    padding: const EdgeInsets.only(bottom: 4),
                    child: _VerticalSubItem(
                      label: labels[i],
                      icon: icon,
                      selected: selected,
                      onTap: () => onChanged(i),
                    ),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _VerticalSubItem extends StatefulWidget {
  const _VerticalSubItem({
    required this.label,
    required this.selected,
    required this.onTap,
    this.icon,
  });

  final String label;
  final IconData? icon;
  final bool selected;
  final VoidCallback onTap;

  @override
  State<_VerticalSubItem> createState() => _VerticalSubItemState();
}

class _VerticalSubItemState extends State<_VerticalSubItem> {
  bool _hover = false;

  @override
  Widget build(BuildContext context) {
    final selected = widget.selected;
    return MouseRegion(
      onEnter: (_) => setState(() => _hover = true),
      onExit: (_) => setState(() => _hover = false),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 150),
        decoration: BoxDecoration(
          color: selected
              ? D4Theme.gold.withValues(alpha: 0.14)
              : (_hover ? D4Theme.surfaceSoft : Colors.transparent),
          borderRadius: BorderRadius.circular(10),
          border: Border(
            left: BorderSide(
              color: selected ? D4Theme.goldBright : Colors.transparent,
              width: 3,
            ),
          ),
        ),
        child: Material(
          color: Colors.transparent,
          child: InkWell(
            onTap: widget.onTap,
            borderRadius: BorderRadius.circular(10),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 11),
              child: Row(
                children: [
                  if (widget.icon != null) ...[
                    Icon(
                      widget.icon,
                      size: 18,
                      color: selected ? D4Theme.goldBright : D4Theme.muted,
                    ),
                    const SizedBox(width: 10),
                  ],
                  Expanded(
                    child: Text(
                      widget.label,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(
                        fontSize: 13,
                        fontWeight: selected ? FontWeight.w600 : FontWeight.w500,
                        color: selected ? D4Theme.goldBright : D4Theme.text,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

/// Fallback étroit : sous-onglets horizontaux défilables.
class ScrollableSubTabs extends StatelessWidget {
  const ScrollableSubTabs({
    super.key,
    required this.labels,
    required this.index,
    required this.onChanged,
    this.icons,
  });

  final List<String> labels;
  final List<IconData>? icons;
  final int index;
  final ValueChanged<int> onChanged;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: D4Theme.surface,
      child: Container(
        height: 48,
        decoration: const BoxDecoration(
          border: Border(bottom: BorderSide(color: D4Theme.line)),
        ),
        child: ListView.separated(
          scrollDirection: Axis.horizontal,
          physics: const BouncingScrollPhysics(),
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
          itemCount: labels.length,
          separatorBuilder: (_, _) => const SizedBox(width: 6),
          itemBuilder: (context, i) {
            final selected = i == index;
            return _HChip(
              label: labels[i],
              icon: icons != null && i < icons!.length ? icons![i] : null,
              selected: selected,
              onTap: () => onChanged(i),
            );
          },
        ),
      ),
    );
  }
}

class _HChip extends StatelessWidget {
  const _HChip({
    required this.label,
    required this.selected,
    required this.onTap,
    this.icon,
  });

  final String label;
  final IconData? icon;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: selected ? D4Theme.gold.withValues(alpha: 0.16) : D4Theme.surfaceSoft,
      borderRadius: BorderRadius.circular(10),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(10),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: selected ? D4Theme.gold : D4Theme.line),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              if (icon != null) ...[
                Icon(icon, size: 14, color: selected ? D4Theme.goldBright : D4Theme.muted),
                const SizedBox(width: 6),
              ],
              Text(
                label,
                style: TextStyle(
                  fontSize: 12.5,
                  fontWeight: selected ? FontWeight.w600 : FontWeight.w500,
                  color: selected ? D4Theme.goldBright : D4Theme.muted,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// Coquille : sous-onglets verticaux (desktop) ou horizontaux (fenêtre étroite).
class SectionScaffold extends StatelessWidget {
  const SectionScaffold({
    super.key,
    required this.labels,
    required this.pages,
    required this.index,
    required this.onIndexChanged,
    this.icons,
    this.sectionTitle,
  }) : assert(labels.length == pages.length);

  final List<String> labels;
  final List<IconData>? icons;
  final List<Widget> pages;
  final int index;
  final ValueChanged<int> onIndexChanged;
  final String? sectionTitle;

  @override
  Widget build(BuildContext context) {
    final safe = index.clamp(0, pages.length - 1);
    // Vertical on desktop; horizontal only for very narrow windows.
    final preferVertical = MediaQuery.sizeOf(context).width >= 640;
    final content = IndexedStack(index: safe, children: pages);

    if (!preferVertical) {
      return Column(
        children: [
          ScrollableSubTabs(
            labels: labels,
            icons: icons,
            index: safe,
            onChanged: onIndexChanged,
          ),
          Expanded(child: content),
        ],
      );
    }

    return Row(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        VerticalSubNav(
          title: sectionTitle,
          labels: labels,
          icons: icons,
          index: safe,
          onChanged: onIndexChanged,
          width: 196,
        ),
        const VerticalDivider(width: 1, color: D4Theme.line),
        Expanded(child: content),
      ],
    );
  }
}
