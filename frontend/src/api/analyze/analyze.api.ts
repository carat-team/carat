// TODO: КОД НИЖЕ ЯВЛЯЕТСЯ ПОКАЗАТЕЛЬНЫМ ПРИМЕРОМ,
// УДАЛИТЬ ВРЕМЕННЫЕ ДАННЫЕ ПЕРЕД ВНЕДРЕНИЕМ ПЕРВЫХ РУЧЕК

import { apiClient } from '../client';
import type { ExampleRequestData, ExampleRequestResponse } from './types';

export const analyzeApi = {
  exampleRequest: async (exampleData: ExampleRequestData) => {
    const response = await apiClient.post<ExampleRequestResponse>('/example/path', exampleData);
    return response.data;
  },
} as const;
