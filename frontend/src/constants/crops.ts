import type { Crop } from '@/types/api';

// Static reference data: the crop types this app covers. Not sourced from
// the backend since it rarely changes and is needed before any API call
// (e.g. to render the crop filter itself).
export const crops: Crop[] = [
  { id: 1, type: 'rice', nameVi: 'Lúa' },
  { id: 2, type: 'coffee', nameVi: 'Cà phê' },
  { id: 3, type: 'vegetable', nameVi: 'Rau màu' },
];
