import 'package:flutter/material.dart';

class PieceSetInfo {
  const PieceSetInfo(this.id, this.label, this.desc);
  final String id;
  final String label;
  final String desc;
}

class BoardThemeInfo {
  const BoardThemeInfo(this.id, this.label, this.light, this.dark);
  final String id;
  final String label;
  final Color light;
  final Color dark;
}

class AppThemeInfo {
  const AppThemeInfo(this.id, this.label, this.bg, this.surface, this.gold);
  final String id;
  final String label;
  final Color bg;
  final Color surface;
  final Color gold;
}

class SoundPackInfo {
  const SoundPackInfo(this.id, this.label, this.desc, this.icon);
  final String id;
  final String label;
  final String desc;
  final IconData icon;
}

/// Au moins 20 sets de pièces (dossiers assets/pieces/id).
const pieceSets = [
  PieceSetInfo('cburnett', 'Classique', 'Staunton Lichess'),
  PieceSetInfo('merida', 'Merida', 'Tournoi net'),
  PieceSetInfo('maestro', 'Maestro', 'Fin et précis'),
  PieceSetInfo('alpha', 'Alpha', 'Minimaliste'),
  PieceSetInfo('fantasy', 'Fantasy', 'Dark fantasy D4'),
  PieceSetInfo('california', 'California', 'Style contemporain'),
  PieceSetInfo('cardinal', 'Cardinal', 'Contour net'),
  PieceSetInfo('staunty', 'Staunty', 'Staunton neo'),
  PieceSetInfo('gioco', 'Gioco', 'Italien'),
  PieceSetInfo('leipzig', 'Leipzig', 'Allemand'),
  PieceSetInfo('anarcandy', 'Anarcandy', 'Coloré audacieux'),
  PieceSetInfo('caliente', 'Caliente', 'Chaud et vif'),
  PieceSetInfo('celtic', 'Celtic', 'Motifs celtiques'),
  PieceSetInfo('chess7', 'Chess7', 'Lignes modernes'),
  PieceSetInfo('chessnut', 'Chessnut', 'Bois chaleureux'),
  PieceSetInfo('companion', 'Companion', 'Doux et lisible'),
  PieceSetInfo('dubrovny', 'Dubrovny', 'Élégance est'),
  PieceSetInfo('fresca', 'Fresca', 'Frais et clair'),
  PieceSetInfo('governor', 'Governor', 'Autoritaire'),
  PieceSetInfo('horsey', 'Horsey', 'Expressif'),
  PieceSetInfo('icpieces', 'IC Pieces', 'Icônes nettes'),
  PieceSetInfo('kaneo', 'Kaneo', 'Design plat'),
  PieceSetInfo('kosal', 'Kosal', 'Traditionnel'),
  PieceSetInfo('mono', 'Mono', 'Monochrome'),
  PieceSetInfo('mpchess', 'MP Chess', 'Pro compact'),
  PieceSetInfo('neo', 'Neo', 'Néo-classique'),
  PieceSetInfo('pixel', 'Pixel', 'Rétro 8-bit'),
  PieceSetInfo('shapes', 'Shapes', 'Géométrique'),
  PieceSetInfo('spatial', 'Spatial', '3D stylisé'),
  PieceSetInfo('tatiana', 'Tatiana', 'Artistique'),
];

/// ≥20 thèmes d’échiquier (couleurs contrastées).
const boardThemes = [
  BoardThemeInfo('classic', 'Classique', Color(0xFFF0D9B5), Color(0xFFB58863)),
  BoardThemeInfo('sanctum', 'Bois', Color(0xFFC4A882), Color(0xFF5A4030)),
  BoardThemeInfo('marble', 'Marbre', Color(0xFFE8E4DC), Color(0xFF6E7480)),
  BoardThemeInfo('midnight', 'Dark', Color(0xFF6A6A74), Color(0xFF2A2A32)),
  BoardThemeInfo('throne', 'Noir & Or', Color(0xFFC4A46A), Color(0xFF3A2A18)),
  BoardThemeInfo('storm', 'Futuriste', Color(0xFF9AA4B4), Color(0xFF2E3644)),
  BoardThemeInfo('eclipse', 'Eclipse', Color(0xFF7A7088), Color(0xFF282030)),
  BoardThemeInfo('molten', 'Fonte', Color(0xFFE08A4A), Color(0xFF5A2810)),
  BoardThemeInfo('phoenix', 'Phoenix', Color(0xFFE0A060), Color(0xFF7A3818)),
  BoardThemeInfo('jade', 'Jade', Color(0xFFA8D0B0), Color(0xFF2E5238)),
  BoardThemeInfo('infernal', 'Infernal', Color(0xFFE07048), Color(0xFF501810)),
  BoardThemeInfo('obsidian', 'Obsidienne', Color(0xFF8A8894), Color(0xFF2A2832)),
  BoardThemeInfo('blue', 'Océan', Color(0xFFDEE3EF), Color(0xFF4B6FA0)),
  BoardThemeInfo('green', 'Forêt', Color(0xFFD5E0C8), Color(0xFF4F7350)),
  BoardThemeInfo('ice', 'Glace', Color(0xFFE8F2F8), Color(0xFF6A8FA8)),
  BoardThemeInfo('coral', 'Corail', Color(0xFFF3D5C8), Color(0xFFB86A5A)),
  BoardThemeInfo('ember', 'Braise', Color(0xFFE8B888), Color(0xFF8A4028)),
  BoardThemeInfo('frostbite', 'Gel', Color(0xFFD8E8F0), Color(0xFF4A6A7A)),
  BoardThemeInfo('bloodstone', 'Sang', Color(0xFFE0B0A8), Color(0xFF6A2828)),
  BoardThemeInfo('celestial', 'Céleste', Color(0xFFD8D0F0), Color(0xFF4A3A7A)),
  BoardThemeInfo('copper', 'Cuivre', Color(0xFFE8C8A0), Color(0xFF8A5030)),
  BoardThemeInfo('crypt', 'Crypte', Color(0xFFB8B0A0), Color(0xFF3A3830)),
  BoardThemeInfo('dragon', 'Dragon', Color(0xFFD0C090), Color(0xFF5A3820)),
  BoardThemeInfo('void', 'Néant', Color(0xFF6A6880), Color(0xFF1A1828)),
  BoardThemeInfo('sandstone', 'Sable', Color(0xFFE8D8B8), Color(0xFFA08050)),
  BoardThemeInfo('venom', 'Venin', Color(0xFFC8E0A8), Color(0xFF3A6030)),
  BoardThemeInfo('valor', 'Valeur', Color(0xFFE0D0B0), Color(0xFF5A4840)),
  BoardThemeInfo('wrought', 'Ferronnerie', Color(0xFFC8C0B0), Color(0xFF484038)),
];

/// 15 packs sonores stylés.
const soundPacks = [
  SoundPackInfo('classic', 'Classique', 'Coup net et clair', Icons.sports_esports),
  SoundPackInfo('wood', 'Bois', 'Plateau en bois massif', Icons.forest),
  SoundPackInfo('glass', 'Verre', 'Cristal cristallin', Icons.wine_bar),
  SoundPackInfo('metal', 'Métal', 'Impact métallique', Icons.hardware),
  SoundPackInfo('soft', 'Doux', 'Discret et feutré', Icons.spa),
  SoundPackInfo('arcade', 'Arcade', 'Rétro 8-bit', Icons.videogame_asset),
  SoundPackInfo('tournament', 'Tournoi', 'Salle de compétition', Icons.emoji_events),
  SoundPackInfo('neon', 'Néon', 'Synthétique futuriste', Icons.bolt),
  SoundPackInfo('stone', 'Pierre', 'Cases de pierre', Icons.landscape),
  SoundPackInfo('crystal', 'Cristal', 'Aigu et brillant', Icons.diamond),
  SoundPackInfo('drum', 'Percussion', 'Battements sourds', Icons.music_note),
  SoundPackInfo('laser', 'Laser', 'Sci-fi énergétique', Icons.flash_on),
  SoundPackInfo('vintage', 'Vintage', 'Ancien radio', Icons.radio),
  SoundPackInfo('royal', 'Royal', 'Noble et plein', Icons.castle),
  SoundPackInfo('stealth', 'Furtif', 'Presque silencieux', Icons.visibility_off),
];

const appThemes = [
  AppThemeInfo('d4_gold', 'D4 Gold', Color(0xFF080605), Color(0xFF12100E), Color(0xFFD4A548)),
  AppThemeInfo('obsidian', 'Obsidian', Color(0xFF0A0A0C), Color(0xFF16161A), Color(0xFFC0B090)),
  AppThemeInfo('classic', 'Classic', Color(0xFF1A1510), Color(0xFF2A2218), Color(0xFFD4A548)),
  AppThemeInfo('tournament', 'Tournament', Color(0xFF101410), Color(0xFF1A201A), Color(0xFFB8A060)),
  AppThemeInfo('midnight', 'Midnight', Color(0xFF0A0C14), Color(0xFF141824), Color(0xFF8AA0D0)),
  AppThemeInfo('graphite', 'Graphite', Color(0xFF121212), Color(0xFF1E1E1E), Color(0xFFB0A898)),
  AppThemeInfo('emerald', 'Emerald', Color(0xFF08120E), Color(0xFF122018), Color(0xFF6CB890)),
  AppThemeInfo('royal', 'Royal', Color(0xFF100810), Color(0xFF1C121C), Color(0xFFD4A0C0)),
  AppThemeInfo('minimal', 'Minimal', Color(0xFF101010), Color(0xFF181818), Color(0xFFC8C0B0)),
  // —— +30 thèmes ——
  AppThemeInfo('aurora', 'Aurora', Color(0xFF0A1218), Color(0xFF121C24), Color(0xFF40E0C0)),
  AppThemeInfo('crimson', 'Crimson', Color(0xFF160A0C), Color(0xFF221214), Color(0xFFE63950)),
  AppThemeInfo('sapphire', 'Sapphire', Color(0xFF0A1020), Color(0xFF121828), Color(0xFF3D6BFF)),
  AppThemeInfo('olive', 'Olive', Color(0xFF12140E), Color(0xFF1C2016), Color(0xFF8BA84A)),
  AppThemeInfo('flamingo', 'Flamingo', Color(0xFF180E14), Color(0xFF24161C), Color(0xFFFF5C9A)),
  AppThemeInfo('steel', 'Steel', Color(0xFF101418), Color(0xFF181E24), Color(0xFF5B8FA8)),
  AppThemeInfo('plum', 'Plum', Color(0xFF140E16), Color(0xFF1E1622), Color(0xFFA060C0)),
  AppThemeInfo('teal', 'Teal', Color(0xFF0A1414), Color(0xFF121E1E), Color(0xFF2EC4B6)),
  AppThemeInfo('charcoal', 'Charcoal', Color(0xFF0E0E0E), Color(0xFF181818), Color(0xFFB0B0B0)),
  AppThemeInfo('honey', 'Honey', Color(0xFF161208), Color(0xFF221C10), Color(0xFFFFC030)),
  AppThemeInfo('indigo', 'Indigo', Color(0xFF0C0E1C), Color(0xFF141628), Color(0xFF6B6BFF)),
  AppThemeInfo('moss', 'Moss', Color(0xFF0E1410), Color(0xFF161E18), Color(0xFF6BAA60)),
  AppThemeInfo('carbon', 'Carbon', Color(0xFF0C0C10), Color(0xFF16161C), Color(0xFF00B4D8)),
  AppThemeInfo('wine', 'Wine', Color(0xFF160A10), Color(0xFF221218), Color(0xFFB04060)),
  AppThemeInfo('electric', 'Electric', Color(0xFF0E0E0A), Color(0xFF181810), Color(0xFFE8FF00)),
  AppThemeInfo('copper', 'Copper', Color(0xFF120E0A), Color(0xFF1E1812), Color(0xFFD08040)),
  AppThemeInfo('neon_pink', 'Neon Pink', Color(0xFF100A10), Color(0xFF1A121A), Color(0xFFFF2E9A)),
  AppThemeInfo('abyss', 'Abyss', Color(0xFF060C14), Color(0xFF0C1620), Color(0xFF1AA0D0)),
  AppThemeInfo('matcha', 'Matcha', Color(0xFF10140C), Color(0xFF1A2014), Color(0xFF88B040)),
  AppThemeInfo('orchid', 'Orchid', Color(0xFF140E16), Color(0xFF1E1622), Color(0xFFD050C0)),
  AppThemeInfo('tokyo', 'Tokyo Night', Color(0xFF1A1B26), Color(0xFF24283B), Color(0xFF7AA2F7)),
  AppThemeInfo('solarized', 'Solarized', Color(0xFF002B36), Color(0xFF073642), Color(0xFF268BD2)),
  AppThemeInfo('gruvbox', 'Gruvbox', Color(0xFF282828), Color(0xFF3C3836), Color(0xFFFE8019)),
  AppThemeInfo('dracula', 'Dracula', Color(0xFF282A36), Color(0xFF21222C), Color(0xFFFF79C6)),
  AppThemeInfo('nord', 'Nord', Color(0xFF2E3440), Color(0xFF3B4252), Color(0xFF88C0D0)),
  AppThemeInfo('cyber', 'Cyber', Color(0xFF070B0D), Color(0xFF0E1518), Color(0xFF00E5C0)),
  AppThemeInfo('amber', 'Amber', Color(0xFF12100A), Color(0xFF1C1810), Color(0xFFFFB020)),
  AppThemeInfo('rose', 'Rose', Color(0xFF140E12), Color(0xFF1E161A), Color(0xFFFF6B9D)),
  AppThemeInfo('matrix', 'Matrix', Color(0xFF050A06), Color(0xFF0A140C), Color(0xFF33FF66)),
  AppThemeInfo('sunset', 'Sunset', Color(0xFF1A0E14), Color(0xFF26161C), Color(0xFFFF5E7A)),
];

BoardThemeInfo boardById(String id) =>
    boardThemes.firstWhere((b) => b.id == id, orElse: () => boardThemes.first);

PieceSetInfo pieceSetById(String id) =>
    pieceSets.firstWhere((p) => p.id == id, orElse: () => pieceSets.first);

SoundPackInfo soundPackById(String id) =>
    soundPacks.firstWhere((s) => s.id == id, orElse: () => soundPacks.first);

AppThemeInfo appThemeById(String id) =>
    appThemes.firstWhere((t) => t.id == id, orElse: () => appThemes.first);
