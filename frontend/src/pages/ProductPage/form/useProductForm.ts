import { useForm } from 'react-hook-form';
import type { ProductFormValues } from './types';

export const useProductForm = () =>
  useForm<ProductFormValues>({
    defaultValues: {
      fullName: '',
      tnVedCode: '3303',
      tnVedCode10: '',
      gtin: '',
      brand: '',
      country: '',
      perfumeryType: '',
      volume: { value: 0, unit: 'мл' },
      packageType: '',
      packMaterial: '',
      standardNumber: [],
      photos: [],
    },
    // Preserve field values when a step unmounts.
    shouldUnregister: false,
  });
