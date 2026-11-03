export type CardStatus = 'draft' | 'on_moderation' | 'published' | 'rejected';

export type ProductState = 'ready_to_order_km';

export type PerfumeryType =
  | 'ДУХИ'
  | 'ДУШИСТАЯ ВОДА'
  | 'ЛАВАНДОВАЯ ВОДА'
  | 'ОДЕКОЛОН'
  | 'ПАРФЮМЕРНАЯ ВОДА'
  | 'СПРЕЙ ДЛЯ ТЕЛА'
  | 'ТУАЛЕТНАЯ ВОДА'
  | 'КОМПЛЕКТ';

export type PhotoAngle = 'front' | 'left' | 'right' | 'back';

export interface ProductPhoto {
  angle: PhotoAngle;
  url?: string;
}

export type ProductTnVedCode10 = '3303001000' | '3303009000';

export type ProductVolumeUnit = 'л' | 'мл' | 'г';

export type ProductStandardNumber = 'ТР ТС 009/2011' | 'ТР ТС 029/2012' | 'ТР ТС 005/2011';

export interface ProductVolume {
  value: number;
  unit: ProductVolumeUnit;
}

export interface Product {
  // строка, т.к. GTIN может начинаться с нуля
  gtin: string;
  createdAt: string;
  state: ProductState;
  status: CardStatus;

  category: string;
  okpd2: string;
  fullName: string;
  tnVedCode: string;
  brand?: string;

  tnVedCode10?: ProductTnVedCode10;
  perfumeryType?: PerfumeryType;
  volume?: ProductVolume;
  country?: string[];
  packageType?: string;
  packMaterial?: string;
  standardNumber?: ProductStandardNumber[];

  photos: ProductPhoto[];
}

export interface ProductListItem {
  gtin: string;
  createdAt: string;
  photoUrl?: string;
  fullName: string;
  category: string;
  packagesCount: number;
  brand?: string;
  state: ProductState;
  status: CardStatus;
}
