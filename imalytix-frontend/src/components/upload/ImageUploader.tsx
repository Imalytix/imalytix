import clsx from "clsx";
import { UploadCloud } from "lucide-react";
import { useRef, useState } from "react";
import SelectedImagePreview from "./SelectedImagePreview";

interface ImageUploaderProps {
  previewUrl: string | null;
  fileName: string | null | undefined;
  onFileSelected: (file: File, previewUrl: string) => void;
}

function fileToDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = () => reject(new Error("미리보기 이미지를 생성할 수 없습니다."));
    reader.readAsDataURL(file);
  });
}

export default function ImageUploader({
  previewUrl,
  fileName,
  onFileSelected,
}: ImageUploaderProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleFiles = async (fileList: FileList | null) => {
    const file = fileList?.[0];
    if (!file) return;
    const dataUrl = await fileToDataUrl(file);
    onFileSelected(file, dataUrl);
  };

  return (
    <div className="grid gap-4 lg:grid-cols-[0.9fr_1.1fr]">
      <div
        className={clsx(
          "rounded-[28px] border border-slate-200 bg-white p-5 transition",
          isDragging ? "border-slate-400 bg-slate-50" : "hover:border-slate-300",
        )}
        onDragOver={(event) => {
          event.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={async (event) => {
          event.preventDefault();
          setIsDragging(false);
          await handleFiles(event.dataTransfer.files);
        }}
      >
        <div className="flex h-full flex-col justify-between gap-5">
          <div className="space-y-4">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl border border-slate-200 bg-slate-50 text-slate-500">
              <UploadCloud className="h-6 w-6" />
            </div>
            <div>
              <div className="text-base font-semibold text-slate-900">이미지 업로드</div>
              <div className="mt-1 text-sm leading-6 text-slate-500">
                JPG, PNG, WEBP 파일을 드래그하거나 버튼으로 선택하세요.
              </div>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={() => inputRef.current?.click()}
              className="rounded-2xl border border-slate-200 bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800"
            >
              파일 선택
            </button>
            <span className="text-xs text-slate-500">기본값: standard / include_child_risk=true / return_bbox=true</span>
          </div>

          <input
            ref={inputRef}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            className="hidden"
            onChange={async (event) => {
              await handleFiles(event.target.files);
              event.currentTarget.value = "";
            }}
          />
        </div>
      </div>

      <div className="rounded-[28px] border border-slate-200 bg-white p-3">
        {previewUrl ? (
          <SelectedImagePreview
            imageUrl={previewUrl}
            fileName={fileName ?? "업로드된 이미지"}
          />
        ) : (
          <div className="flex min-h-[320px] items-center justify-center rounded-[24px] border border-dashed border-slate-200 bg-slate-50 text-sm text-slate-400">
            이미지를 선택하면 여기에 미리보기가 표시됩니다.
          </div>
        )}
      </div>
    </div>
  );
}
