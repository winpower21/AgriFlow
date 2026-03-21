// Curated pastel color palette for stage cards
// HSL saturation ~35-55%, lightness ~65-80% — readable with dark text on card backgrounds

export const STAGE_COLORS = [
  // Greens
  "#A8D8B9", // soft sage green
  "#9DCFB0", // medium sage
  "#B8E0C8", // light mint green
  "#A3D4A0", // soft leaf green
  "#B3DDB3", // pale spring green

  // Teals & Cyans
  "#94CEC8", // soft teal
  "#A4D4D0", // light teal
  "#9ACFCF", // medium cyan-teal
  "#A8DADA", // pale aqua
  "#8DC8C8", // dusty cyan

  // Blues
  "#A3C4E8", // soft sky blue
  "#9BB8E0", // medium periwinkle
  "#B0C8F0", // light cornflower blue
  "#A8BEDD", // muted blue
  "#94AFDB", // dusty blue

  // Purples & Lavenders
  "#C0B0E8", // soft lavender
  "#BCA8E0", // medium lavender
  "#CABCD8", // dusty purple
  "#C8B4E0", // pale violet
  "#B8A8D8", // muted mauve

  // Pinks & Roses
  "#F4B9C2", // soft pink
  "#EDB0BC", // medium blush
  "#F0C0CC", // light rose
  "#E8A8B8", // dusty pink
  "#F0B0C4", // medium pink

  // Reds & Corals
  "#F0A8A0", // soft coral
  "#EBA090", // medium salmon
  "#F4B0A8", // light coral
  "#E89898", // muted red
  "#F0A898", // peach-coral

  // Oranges & Ambers
  "#F4C898", // soft amber
  "#F0BC88", // medium peach
  "#F4D0A0", // light apricot
  "#ECC090", // dusty orange
  "#F4C8A0", // soft peach

  // Yellows
  "#F4E098", // soft yellow
  "#F0D888", // medium butter
  "#F4E8A0", // pale lemon
  "#ECD890", // dusty gold
  "#F4DCA0", // warm cream-yellow
];

// Curated Bootstrap Icons for agricultural processing stages
export const STAGE_ICONS = [
  // Harvest / Growth
  { class: "bi-flower1", label: "Flower" },
  { class: "bi-flower2", label: "Flower Variant" },
  { class: "bi-flower3", label: "Flower Alt" },
  { class: "bi-leaf", label: "Leaf" },
  { class: "bi-leaf-fill", label: "Leaf" },
  { class: "bi-tree", label: "Tree" },

  // Cleaning / Water
  { class: "bi-droplet", label: "Droplet" },
  { class: "bi-droplet-fill", label: "Droplet" },
  { class: "bi-moisture", label: "Moisture" },

  // Drying / Heat
  { class: "bi-sun", label: "Sun" },
  { class: "bi-brightness-high", label: "Brightness" },
  { class: "bi-fire", label: "Fire" },
  { class: "bi-thermometer", label: "Thermometer" },
  { class: "bi-snow", label: "Snow / Cold" },
  { class: "bi-lightning", label: "Lightning" },

  // Bagging / Packing
  { class: "bi-bag", label: "Bag" },
  { class: "bi-box-seam", label: "Box Sealed" },
  { class: "bi-box", label: "Box" },
  { class: "bi-archive", label: "Archive" },

  // Grading / Quality
  // { class: "bi-trophy", label: "Trophy" },
  { class: "bi-star", label: "Star" },
  // { class: "bi-award", label: "Award" },
  { class: "bi-funnel", label: "Funnel" },

  // Retail / Sales
  { class: "bi-shop", label: "Shop" },
  { class: "bi-cart", label: "Cart" },
  { class: "bi-basket", label: "Basket" },

  // Processing
  { class: "bi-scissors", label: "Scissors" },
  { class: "bi-gear", label: "Gear" },
  { class: "bi-tools", label: "Tools" },

  // Transport / Dispatch
  { class: "bi-truck", label: "Truck" },
  { class: "bi-send", label: "Send" },

  // Grades
  { class: "bi-1-circle-fill", label: "Grade 1" },
  { class: "bi-2-circle-fill", label: "Grade 2" },
  { class: "bi-3-circle-fill", label: "Grade 3" },
  { class: "bi-4-circle-fill", label: "Grade 4" },
  { class: "bi-5-circle-fill", label: "Grade 5" },

  // Storage / Collection
  { class: "bi-collection", label: "Collection" },
  { class: "bi-trash", label: "Waste" },
];

export const DEFAULT_STAGE_COLOR = "#B0B8C1";
export const DEFAULT_STAGE_ICON = "bi-layers";
