import { IconUpload, IconX } from '@tabler/icons-react';
import { useEffect, useId, useState } from 'react';

type PhotoFileFieldProps = {
  file: File | null;
  onChange: (file: File | null) => void;
};

export const PhotoFileField = ({ file, onChange }: PhotoFileFieldProps) => {
  const inputId = useId();
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  // Читаем выбранный файл, чтобы показать маленькое превью
  useEffect(() => {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => setPreviewUrl(typeof reader.result === 'string' ? reader.result : null);
    reader.readAsDataURL(file);
    return () => reader.abort();
  }, [file]);

  if (file && previewUrl) {
    return (
      <div className="flex h-12 items-center gap-3 rounded-md border border-solid border-[#dde4e9] bg-white px-2">
        <img src={previewUrl} alt={file.name} className="size-9 shrink-0 rounded-sm object-cover" />
        <span className="min-w-0 flex-1 truncate text-sm">{file.name}</span>
        <button
          type="button"
          aria-label="Убрать файл"
          className="cursor-pointer text-gray-400 hover:text-foreground"
          onClick={() => onChange(null)}
        >
          <IconX />
        </button>
      </div>
    );
  }

  return (
    <label
      htmlFor={inputId}
      className="flex h-12 cursor-pointer items-center justify-center gap-1.5 rounded-md border border-solid border-gray-200 bg-white text-xs font-medium"
    >
      <IconUpload />
      Загрузить файл
      <input
        id={inputId}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        className="sr-only"
        onChange={(e) => onChange(e.target.files?.[0] ?? null)}
      />
    </label>
  );
};
