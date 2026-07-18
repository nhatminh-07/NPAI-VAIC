export interface QuarterOption {
  value: string; // dùng làm giá trị gửi lên API, vd "2026-Q3"
  labelVi: string; // hiển thị cho người dùng, vd "Quý 3/2026"
}

// Tự sinh ra quý hiện tại + `count - 1` quý liền trước đó (mới nhất trước), để
// dropdown chọn kỳ báo cáo ở trang /dashboard luôn cập nhật mà không cần sửa code
// mỗi khi sang quý mới. Mặc định lấy 4 quý gần nhất tính từ ngày hiện tại.
export function recentQuarterOptions(count = 4, from = new Date()): QuarterOption[] {
  const options: QuarterOption[] = [];
  let year = from.getFullYear();
  let quarter = Math.floor(from.getMonth() / 3) + 1;

  for (let i = 0; i < count; i++) {
    options.push({ value: `${year}-Q${quarter}`, labelVi: `Quý ${quarter}/${year}` });
    quarter -= 1;
    if (quarter === 0) {
      quarter = 4;
      year -= 1;
    }
  }

  return options;
}
