/**
 * Application state management models
 */

import { StockData } from './api.models';
import { ChartDisplayMode, ChartType } from './chart.models';

/**
 * Global application state
 */
export interface AppState {
  auth: {
    isAuthenticated: boolean;
    token: string | null;
    username: string | null;
  };
  dashboard: DashboardState;
}

/**
 * Dashboard component state
 */
export interface DashboardState {
  selectedMarket: string;
  selectedDisplayMode: ChartDisplayMode;
  selectedChartType: ChartType;
  goldenCrosses: string[];
  stockDataMap: Map<string, StockData>;
  isLoading: boolean;
  error: string | null;
  lastRefresh: Date | null;
}
