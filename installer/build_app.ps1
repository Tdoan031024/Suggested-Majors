# ============================================================
#  build_app.ps1 – Script tự động build HUIT GUI thành .exe
#  Chạy: .\installer\build_app.ps1
# ============================================================

# Lấy thư mục gốc của dự án (lùi 1 cấp từ installer/)
$INSTALLER_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$ROOT = Split-Path -Parent $INSTALLER_DIR
Set-Location $ROOT

$PYTHON  = "$ROOT\.venv\Scripts\python.exe"
$PIP     = "$ROOT\.venv\Scripts\pip.exe"
$PYINST  = "$ROOT\.venv\Scripts\pyinstaller.exe"

Write-Host ""
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "  HUIT – Build Desktop App  (PyInstaller)" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan

# ── Bước 1: Kiểm tra PyInstaller ────────────────────────────
Write-Host "`n[1/5] Kiểm tra PyInstaller..." -ForegroundColor Yellow
if (-not (Test-Path $PYINST)) {
    Write-Host "     Đang cài đặt PyInstaller..." -ForegroundColor Gray
    & $PIP install pyinstaller --quiet
    if ($LASTEXITCODE -ne 0) { 
        Write-Host "FAILED! Không thể cài PyInstaller." -ForegroundColor Red
        exit 1 
    }
}
Write-Host "     PyInstaller đã sẵn sàng." -ForegroundColor Green

# ── Bước 2: Dọn dẹp ─────────────────────────────────────────
Write-Host "`n[2/5] Dọn dẹp build cũ..." -ForegroundColor Yellow
@("build", "dist") | ForEach-Object {
    $target = Join-Path $ROOT $_
    if (Test-Path $target) {
        Remove-Item $target -Recurse -Force
        Write-Host "     Đã xóa /$($_)" -ForegroundColor Gray
    }
}
Write-Host "     Dọn dẹp xong." -ForegroundColor Green

# ── Bước 3: Biên dịch ───────────────────────────────────────
Write-Host "`n[3/5] Đang biên dịch (vui lòng đợi)..." -ForegroundColor Yellow
$SPEC_FILE = Join-Path $ROOT "installer\huit_app.spec"
& $PYTHON -m PyInstaller $SPEC_FILE --clean --noconfirm --log-level WARN

if ($LASTEXITCODE -ne 0) {
    Write-Host "LỖI: Biên dịch thất bại!" -ForegroundColor Red
    exit 1
}
Write-Host "     Biên dịch thành công!" -ForegroundColor Green

# ── Bước 4: Kiểm tra kết quả ────────────────────────────────
Write-Host "`n[4/5] Kiểm tra thư mục đầu ra..." -ForegroundColor Yellow
$DIST_APP = Join-Path $ROOT "dist\HUIT_GoiYNganh"
$EXE = Join-Path $DIST_APP "HUIT_GoiYNganh.exe"

if (Test-Path $EXE) {
    $size = [math]::Round((Get-Item $EXE).Length / 1MB, 1)
    Write-Host "     File chạy: $EXE" -ForegroundColor Green
    Write-Host "     Kích thước: ${size} MB" -ForegroundColor Green
} else {
    Write-Host "LỖI: Không tìm thấy file .exe!" -ForegroundColor Red
    exit 1
}

# ── Bước 5: Hoàn tất ────────────────────────────────────────
Write-Host "`n[5/5] Hoàn tất quá trình build!" -ForegroundColor Yellow
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "  THƯ MỤC ĐẦU RA: dist\HUIT_GoiYNganh\"
Write-Host "  - File chính: HUIT_GoiYNganh.exe"
Write-Host "  - Thư mục models: Chứa các file .pkl"
Write-Host "  - Dữ liệu: DXDuong.xlsx"
Write-Host "-----------------------------------------------------"
Write-Host "  LƯU Ý: Khi copy cho máy khác, hãy nén cả thư mục"
Write-Host "  dist\HUIT_GoiYNganh thành file .zip"
Write-Host "=====================================================" -ForegroundColor Cyan

Write-Host ""
$choice = Read-Host "Bạn có muốn mở thư mục kết quả không? (y/n)"
if ($choice -eq 'y') {
    Start-Process explorer.exe $DIST_APP
}
