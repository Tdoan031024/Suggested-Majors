# -*- coding: utf-8 -*-
"""
GIAO DIỆN NHẬP ĐIỂM HỌC BẠ THPT
Cho phép người dùng chọn tổ hợp và nhập điểm 5 học kỳ
"""

from hoc_ba_analyzer import HocBaAnalyzer, TO_HOP_MON, NGANH_TO_HOP

# Mapping nhóm ngành 9 nhóm (đồng nhất với DGNL)
NGUYEN_VONG_MAP = {
    # Alias ngắn
    'CNTT': ['7480201', '7480202', '7460108', '7340205'],
    'Kinh doanh': ['7340101', '7340115', '7340120', '7340122', '7340129'],
    'Kỹ thuật': ['7510202', '7510203', '7520115', '7510301', '7510303'],
    'Thực phẩm - Môi trường': ['7540101', '7540106', '7540105', '7819009', '7819010', '7340129'],
    'Tài chính': ['7340301', '7340201', '7340205'],
    'Hóa sinh': ['7510401', '7510406', '7850101', '7420201', '7510402'],
    'Luật - Ngôn ngữ': ['7380101', '7380107', '7220201', '7220204'],
    'Logistics': ['7510605', '7340123', '7540204'],
    'Du lịch': ['7810101', '7810103', '7810201', '7810202'],

    # Tên đầy đủ từ menu (không emoji)
    'Công nghệ – Chế biến – Thực phẩm': ['7540101', '7540106', '7540105', '7819009', '7819010', '7340129'],
    'Kỹ thuật – Cơ khí – Tự động hóa': ['7510202', '7510203', '7520115', '7510301', '7510303'],
    'Hóa học – Sinh học – Môi trường – Vật liệu': ['7510401', '7510406', '7850101', '7420201', '7510402'],
    'Công nghệ thông tin – Trí tuệ nhân tạo – Dữ liệu': ['7480201', '7480202', '7460108', '7340205'],
    'Kinh doanh – Quản trị – Marketing': ['7340101', '7340115', '7340120', '7340122', '7340129'],
    'Kế toán – Tài chính – Ngân hàng': ['7340301', '7340201', '7340205'],
    'Logistics – Quản lý chuỗi cung ứng – Kinh doanh chuyên biệt': ['7510605', '7340123', '7540204'],
    'Luật – Xã hội – Ngôn ngữ': ['7380101', '7380107', '7220201', '7220204'],
    'Du lịch – Nhà hàng – Khách sạn – Dịch vụ': ['7810101', '7810103', '7810201', '7810202']
}

def show_nguyen_vong_menu():
    """Hiển thị menu chọn nhóm ngành (đồng nhất với DGNL)"""
    print(f"\n🎯 CHỌN NHÓM NGÀNH ƯA THÍCH (để trống nếu xem tất cả):")
    print("   🧪 1. Công nghệ – Chế biến – Thực phẩm")
    print("   ⚙️  2. Kỹ thuật – Cơ khí – Tự động hóa")
    print("   🌿 3. Hóa học – Sinh học – Môi trường – Vật liệu")
    print("   💻 4. Công nghệ thông tin – Trí tuệ nhân tạo – Dữ liệu")
    print("   💼 5. Kinh doanh – Quản trị – Marketing")
    print("   💰 6. Kế toán – Tài chính – Ngân hàng")
    print("   🚚 7. Logistics – Quản lý chuỗi cung ứng – Kinh doanh chuyên biệt")
    print("   ⚖️  8. Luật – Xã hội – Ngôn ngữ")
    print("   🏨 9. Du lịch – Nhà hàng – Khách sạn – Dịch vụ")
    print("\n   📝 Hoặc dùng tên rút gọn: CNTT, Kinh doanh, Kỹ thuật, Thực phẩm - Môi trường, Tài chính, Hóa sinh, Logistics, Luật - Ngôn ngữ, Du lịch")

def chon_nguyen_vong():
    """Cho phép người dùng chọn nhóm ngành (đồng nhất với DGNL)"""
    show_nguyen_vong_menu()

    nhom_mapping = {
        '1': 'Công nghệ – Chế biến – Thực phẩm',
        '2': 'Kỹ thuật – Cơ khí – Tự động hóa', 
        '3': 'Hóa học – Sinh học – Môi trường – Vật liệu',
        '4': 'Công nghệ thông tin – Trí tuệ nhân tạo – Dữ liệu',
        '5': 'Kinh doanh – Quản trị – Marketing',
        '6': 'Kế toán – Tài chính – Ngân hàng',
        '7': 'Logistics – Quản lý chuỗi cung ứng – Kinh doanh chuyên biệt',
        '8': 'Luật – Xã hội – Ngôn ngữ',
        '9': 'Du lịch – Nhà hàng – Khách sạn – Dịch vụ'
    }

    raw = input("\nNhập số thứ tự (1-9) hoặc tên nhóm: ").strip()
    if raw in nhom_mapping:
        return nhom_mapping[raw]
    # Trả thẳng chuỗi người dùng nhập (cho phép alias)
    return raw

def show_to_hop_menu():
    """Hiển thị menu chọn tổ hợp môn (tất cả)"""
    print(f"\n📚 CHỌN TỔ HỢP MÔN XÉT TUYỂN:")
    print("="*60)

    to_hop_groups = {
        'Khối A (Toán - Lý - Hóa/Anh)': ['A00', 'A01'],
        'Khối B (Toán - Hóa - Sinh/Anh)': ['B00', 'B08'],
        'Khối C (Văn - Sử - Địa)': ['C00', 'C01', 'C02', 'C03', 'C14'],
        'Khối D (Toán - Văn - Anh)': ['D01', 'D07', 'D09', 'D14', 'D15'],
        'Khối X (Tin học)': ['X26']
    }

    for group_name, to_hops in to_hop_groups.items():
        print(f"\n🎯 {group_name}:")
        for to_hop in to_hops:
            if to_hop in TO_HOP_MON:
                mon_hoc = ' - '.join(TO_HOP_MON[to_hop])
                print(f"   {to_hop}: {mon_hoc}")

def chon_to_hop():
    """Cho phép người dùng chọn tổ hợp"""
    show_to_hop_menu()
    
    while True:
        to_hop = input(f"\n📝 Nhập mã tổ hợp (VD: D01, A00, B00...): ").strip().upper()
        
        if to_hop in TO_HOP_MON:
            mon_hoc = TO_HOP_MON[to_hop]
            print(f"✅ Đã chọn tổ hợp {to_hop}: {' - '.join(mon_hoc)}")
            return to_hop, mon_hoc
        else:
            print("❌ Tổ hợp không hợp lệ! Vui lòng chọn lại.")
            
            # Gợi ý các tổ hợp phổ biến
            print("💡 Các tổ hợp phổ biến: D01, A00, A01, B00, C00")

def _resolve_group_key(user_input: str) -> str | None:
    """Tìm khóa nhóm trong NGUYEN_VONG_MAP theo tên hoặc alias (so khớp mờ)."""
    if not user_input:
        return None
    if user_input in NGUYEN_VONG_MAP:
        return user_input
    ui = user_input.lower()
    # match by substring either way
    for key in NGUYEN_VONG_MAP:
        k = key.lower()
        if ui in k or k in ui:
            return key
    return None

def _to_hops_for_group(group_key: str) -> set:
    """Tập các tổ hợp có trong các ngành thuộc nhóm group_key."""
    allowed = set()
    majors = NGUYEN_VONG_MAP.get(group_key, [])
    for code in majors:
        info = NGANH_TO_HOP.get(code)
        if info:
            allowed.update(info.get('to_hop', []))
    return allowed

def show_to_hop_menu_for_group(group_key: str):
    """Hiển thị các tổ hợp chỉ thuộc nhóm ngành đã chọn."""
    all_groups = {
        'Khối A (Toán - Lý - Hóa/Anh)': ['A00', 'A01'],
        'Khối B (Toán - Hóa - Sinh/Anh)': ['B00', 'B08'],
        'Khối C (Văn - Sử - Địa)': ['C00', 'C01', 'C02', 'C03', 'C14'],
        'Khối D (Toán - Văn - Anh)': ['D01', 'D07', 'D09', 'D14', 'D15'],
        'Khối X (Tin học)': ['X26']
    }
    allowed = _to_hops_for_group(group_key)

    print(f"\n📚 CHỌN TỔ HỢP THUỘC NHÓM: {group_key}")
    print("="*60)
    count = 0
    for group_name, to_hops in all_groups.items():
        filtered = [th for th in to_hops if th in allowed]
        if not filtered:
            continue
        print(f"\n🎯 {group_name}:")
        for to_hop in filtered:
            mon_hoc = ' - '.join(TO_HOP_MON[to_hop])
            print(f"   {to_hop}: {mon_hoc}")
            count += 1
    if count == 0:
        print("⚠️ Nhóm này hiện chưa có tổ hợp nào được mở. Hiển thị tất cả tổ hợp để bạn chọn.")
        show_to_hop_menu()

def chon_to_hop_theo_nhom(group_key: str):
    """Chọn tổ hợp nhưng giới hạn theo nhóm ngành đã chọn."""
    allowed = _to_hops_for_group(group_key)
    if allowed:
        show_to_hop_menu_for_group(group_key)
    else:
        show_to_hop_menu()

    while True:
        to_hop = input(f"\n📝 Nhập mã tổ hợp (VD: D01, A00, B00...): ").strip().upper()
        if to_hop in TO_HOP_MON and (not allowed or to_hop in allowed):
            mon_hoc = TO_HOP_MON[to_hop]
            print(f"✅ Đã chọn tổ hợp {to_hop}: {' - '.join(mon_hoc)}")
            return to_hop, mon_hoc
        else:
            if allowed:
                print("❌ Tổ hợp không thuộc nhóm đã chọn hoặc không hợp lệ! Vui lòng chọn lại.")
            else:
                print("❌ Tổ hợp không hợp lệ! Vui lòng chọn lại.")
            print("💡 Gợi ý: ", ", ".join(sorted(allowed)) if allowed else "D01, A00, A01, B00, C00")

def nhap_diem_5_hk(mon_hoc):
    """Nhập điểm 5 học kỳ cho 3 môn"""
    print(f"\n📊 NHẬP ĐIỂM 5 HỌC KỲ THPT:")
    print("💡 Nhập điểm trung bình các học kỳ (thang điểm 10)")
    print("="*60)
    
    hoc_ky = ['HK1 Lớp 10', 'HK2 Lớp 10', 'HK1 Lớp 11', 'HK2 Lớp 11', 'HK1 Lớp 12']
    diem_5_hk = {}
    
    for i, mon in enumerate(mon_hoc):
        print(f"\n📝 Môn {mon}:")
        diem_mon = []
        
        for hk in hoc_ky:
            while True:
                try:
                    diem = float(input(f"   {hk}: "))
                    if 0 <= diem <= 10:
                        diem_mon.append(diem)
                        break
                    else:
                        print("   ❌ Điểm phải từ 0-10!")
                except ValueError:
                    print("   ❌ Vui lòng nhập số hợp lệ!")
        
        diem_5_hk[f'mon{i+1}'] = diem_mon
        tb_mon = sum(diem_mon) / 5
        print(f"   📊 Điểm TB 3 năm: {tb_mon:.2f}")
    
    return diem_5_hk

def nhap_diem_nhanh(mon_hoc):
    """Nhập nhanh điểm trung bình 3 năm của từng môn"""
    print(f"\n⚡ NHẬP NHANH ĐIỂM TRUNG BÌNH 3 NĂM:")
    print("💡 Nhập điểm trung bình 3 năm THPT của từng môn (thang điểm 10)")
    print("="*60)
    
    diem_5_hk = {}
    
    for i, mon in enumerate(mon_hoc):
        while True:
            try:
                diem_tb = float(input(f"📝 Điểm TB 3 năm môn {mon}: "))
                if 0 <= diem_tb <= 10:
                    # Tạo điểm giả cho 5 học kỳ (đều bằng điểm TB)
                    diem_5_hk[f'mon{i+1}'] = [diem_tb] * 5
                    break
                else:
                    print("❌ Điểm phải từ 0-10!")
            except ValueError:
                print("❌ Vui lòng nhập số hợp lệ!")
    
    return diem_5_hk

def show_nganh_phu_hop(to_hop, nguyen_vong=None):
    """Hiển thị các ngành phù hợp với tổ hợp, có thể lọc theo nhóm ngành."""
    nganh_phu_hop = []
    majors_filter = None
    if nguyen_vong:
        key = _resolve_group_key(nguyen_vong)
        if key:
            majors_filter = set(NGUYEN_VONG_MAP.get(key, []))

    for ma_nganh, info in NGANH_TO_HOP.items():
        if to_hop in info['to_hop']:
            if majors_filter is None or ma_nganh in majors_filter:
                nganh_phu_hop.append(f"{ma_nganh}: {info['ten_nganh']}")

    if nganh_phu_hop:
        header = f"\n🎯 CÁC NGÀNH PHÙ HỢP VỚI TỔ HỢP {to_hop}"
        if nguyen_vong:
            header += f" (thuộc nhóm {nguyen_vong})"
        print(header + ":")
        print("="*60)
        for i, nganh in enumerate(nganh_phu_hop, 1):
            print(f"{i:2d}. {nganh}")
        print(f"\n📊 Tổng cộng: {len(nganh_phu_hop)} ngành")

def nhap_diem_uu_tien():
    """Nhập điểm ưu tiên khu vực và đối tượng cho học bạ"""
    print(f"\n🎯 ĐIỂM ƯU TIÊN (NẾU CÓ):")
    print("="*40)
    
    co_uu_tien = input("Bạn có điểm ưu tiên khu vực/đối tượng? (y/n): ").lower().strip()
    
    diem_kv = 0
    diem_dt = 0
    
    if co_uu_tien == 'y':
        print("\n📍 ĐIỂM ƯU TIÊN KHU VỰC:")
        print("   • Khu vực 1: 0 điểm")
        print("   • Khu vực 2-NT: 0.25 điểm") 
        print("   • Khu vực 2: 0.5 điểm")
        print("   • Khu vực 3: 1 điểm")
        
        khu_vuc = input("Nhập khu vực (1/2-NT/2/3): ").strip().upper()
        kv_mapping = {
            '1': 0,
            '2-NT': 0.25,
            '2': 0.5,
            '3': 1
        }
        diem_kv = kv_mapping.get(khu_vuc, 0)
        
        print("\n👥 ĐIỂM ƯU TIÊN ĐỐI TƯỢNG:")
        print("   • Không ưu tiên: 0 điểm")
        print("   • Dân tộc thiểu số: 1 điểm")
        print("   • Con liệt sĩ: 2 điểm")
        print("   • Thương binh: 1-2 điểm")
        
        doi_tuong = input("Nhập đối tượng (0/1/2): ").strip()
        dt_mapping = {
            '0': 0,
            '1': 1,
            '2': 2
        }
        diem_dt = dt_mapping.get(doi_tuong, 0)
        
        if diem_kv > 0 or diem_dt > 0:
            print(f"\n✅ ĐIỂM ƯU TIÊN:")
            print(f"   🏠 Khu vực: +{diem_kv} điểm")
            print(f"   👥 Đối tượng: +{diem_dt} điểm")
            print(f"   📊 Tổng cộng: +{diem_kv + diem_dt} điểm")
    
    return diem_kv, diem_dt

def goi_y_hoc_ba_main():
    """Hàm chính cho gợi ý dựa trên học bạ"""
    print("\n" + "="*80)
    print("📚 HỆ THỐNG GỢI Ý NGÀNH NGHỀ DỰA TRÊN HỌC BẠ THPT")
    print("="*80)
    
    print("📝 Sử dụng công thức HUIT:")
    print("   • ĐHB = ĐHBM1 + ĐHBM2 + ĐHBM3 + Điểm ưu tiên")
    print("   • Điểm mỗi môn = TB(HK1_10, HK2_10, HK1_11, HK2_11, HK1_12)")
    print("   • Thang điểm 30 - Random Forest + Naive Bayes (dùng model đã huấn luyện sẵn)")
    
    # Bước 1: Chọn nhóm ngành mong muốn
    nguyen_vong = chon_nguyen_vong()
    group_key = _resolve_group_key(nguyen_vong) if nguyen_vong else None

    # Bước 2: Chọn tổ hợp môn (lọc theo nhóm nếu có)
    if group_key:
        to_hop, mon_hoc = chon_to_hop_theo_nhom(group_key)
    else:
        to_hop, mon_hoc = chon_to_hop()

    # Hiển thị ngành phù hợp (theo nhóm nếu có)
    show_nganh_phu_hop(to_hop, nguyen_vong if group_key else None)
    
    # Bước 3: Chọn cách nhập điểm
    print(f"\n📋 CÁCH NHẬP ĐIỂM:")
    print("1. 📊 Nhập chi tiết 5 học kỳ (chính xác)")
    print("2. ⚡ Nhập nhanh điểm TB 3 năm (ước tính)")
    
    cach_nhap = input("\nChọn cách nhập (1/2): ").strip()
    
    if cach_nhap == '1':
        diem_5_hk = nhap_diem_5_hk(mon_hoc)
    else:
        diem_5_hk = nhap_diem_nhanh(mon_hoc)
    
    # Bước 4: Tính điểm học bạ
    analyzer = HocBaAnalyzer()
    diem_hb_info = analyzer.tinh_diem_hoc_ba(to_hop, diem_5_hk)
    
    if not diem_hb_info:
        print("❌ Lỗi tính điểm học bạ!")
        return
    
    # Hiển thị kết quả tính điểm
    print(f"\n✅ KẾT QUẢ TÍNH ĐIỂM HỌC BẠ:")
    print("="*60)
    print(f"📚 Tổ hợp: {diem_hb_info['to_hop']} ({' - '.join(diem_hb_info['mon_hoc'])})")
    print(f"📊 Điểm TB môn {diem_hb_info['mon_hoc'][0]}: {diem_hb_info['diem_tb_mon1']}")
    print(f"📊 Điểm TB môn {diem_hb_info['mon_hoc'][1]}: {diem_hb_info['diem_tb_mon2']}")
    print(f"📊 Điểm TB môn {diem_hb_info['mon_hoc'][2]}: {diem_hb_info['diem_tb_mon3']}")
    print(f"🎯 ĐIỂM HỌC BẠ: {diem_hb_info['diem_hb']}")
    
    # Đánh giá mức độ cạnh tranh
    diem_hb = diem_hb_info['diem_hb']
    if diem_hb >= 8.5:
        muc_do = "Xuất sắc - Cơ hội cao"
        icon = "🏆"
    elif diem_hb >= 7.5:
        muc_do = "Khá - Cơ hội tốt"
        icon = "🥈"
    elif diem_hb >= 6.5:
        muc_do = "Trung bình - Cần cố gắng"
        icon = "🥉"
    else:
        muc_do = "Yếu - Cần cải thiện"
        icon = "📈"
    
    print(f"{icon} Mức độ cạnh tranh: {muc_do}")
    
    # Bước 5: Gợi ý ngành nghề
    print(f"\n🤖 ĐANG CHẠY MÔ HÌNH MACHINE LEARNING...")
    print(f"🔄 Random Forest + Naive Bayes đang phân tích (từ models/hocba_models.pkl)...")
    
    try:
        if not analyzer.load_models():
            print("❌ Không thể load ML models! Hãy chạy training/train_hocba_models.py để tạo models/hocba_models.pkl")
            return

        results = analyzer.predict_nganh(diem_hb_info, top_k=10, nguyen_vong=(group_key or nguyen_vong))

        if results:
            if nguyen_vong:
                print(f"\n🎯 TOP 10 NGÀNH GỢI Ý CHO TỔ HỢP {to_hop} - NHÓM {nguyen_vong.upper()}:")
            else:
                print(f"\n🎯 TOP 10 NGÀNH GỢI Ý CHO TỔ HỢP {to_hop} - TẤT CẢ NGÀNH:")
            print("="*80)
            
            for i, result in enumerate(results, 1):
                phu_hop_icon = "✅" if result['to_hop_phu_hop'] else "⚠️"
                
                # Thêm icon cho ngành thuộc nhóm mong muốn
                if result.get('thuoc_nhom_mong_muon', False):
                    nganh_icon = "🎯"  # Ngành thuộc nhóm mong muốn
                else:
                    nganh_icon = "📊"  # Ngành khác
                
                print(f"{i:2d}. {phu_hop_icon}{nganh_icon} {result['ten_nganh']:<43} {result['xac_suat']:5.1f}%")
            
            print("="*80)
            print(f"✅ Phù hợp với tổ hợp | ⚠️ Không hoàn toàn phù hợp")
            if nguyen_vong:
                print(f"🎯 Nhóm ngành mong muốn | 📊 Ngành khác")
                print(f"💡 Ưu tiên các ngành có icon 🎯 - phù hợp với sở thích {nguyen_vong}")
            print(f"🎯 Với điểm {diem_hb}, bạn có cơ hội tốt với các ngành được đánh dấu ✅")
            
        else:
            print("❌ Không tìm thấy ngành phù hợp!")

    except Exception as e:
        print(f"❌ Lỗi ML model: {e}")

if __name__ == "__main__":
    goi_y_hoc_ba_main()