// TODO: Review this contract against the completed step forms.

import type { ProductVolume } from '@/types';

// UI form values. Add conversion to REST attributes during API integration.
export type ProductFormValues = {
  fullName: string;
  tnVedCode: string;
  tnVedCode10: string;
  gtin: string;
  brand: string;
  country: string;
  perfumeryType: string;
  volume: ProductVolume;
  packageType: string;
  packMaterial: string;
  standardNumber: string[];
  photos: {
    file: File | null;
    perspective: string;
    packageId: string;
  }[];
};

// Each step receives its form slice. onChange supplies a shallow partial update.
export type ProductStepProps<Values> = {
  values: Readonly<Values>;
  onChange: (patch: Partial<Values>) => void;
  disabled?: boolean;
};

export type RegistrationStepProps = ProductStepProps<
  Pick<ProductFormValues, 'fullName' | 'tnVedCode' | 'tnVedCode10' | 'gtin' | 'brand'>
>;

export type InfoStepProps = ProductStepProps<
  Pick<
    ProductFormValues,
    'country' | 'perfumeryType' | 'volume' | 'packageType' | 'packMaterial' | 'standardNumber'
  >
>;

export type PhotosStepProps = ProductStepProps<Pick<ProductFormValues, 'photos'>>;
