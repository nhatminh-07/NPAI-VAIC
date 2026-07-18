import type { Crop } from '@/types/api';

// Dữ liệu tĩnh: danh sách loại cây trồng mà ứng dụng hỗ trợ. Không lấy từ backend vì
// hiếm khi thay đổi, và cần có sẵn TRƯỚC khi gọi API (vd để render dropdown lọc cây
// trồng ngay khi trang vừa mở, chưa cần chờ response nào).
// `id` ở đây dùng làm cropId khi gọi getMarketPrice()/getDashboard() - phải khớp với
// id mà backend hiểu, không được tự đổi số tuỳ ý.
export const crops: Crop[] = [
  { id: 1, type: 'rice', nameVi: 'Lúa' },
  { id: 2, type: 'coffee', nameVi: 'Cà phê' },
  { id: 3, type: 'vegetable', nameVi: 'Rau màu' },
];
