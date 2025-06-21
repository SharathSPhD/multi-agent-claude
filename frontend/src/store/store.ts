import { configureStore } from '@reduxjs/toolkit';
import agentsSlice from './slices/agentsSlice';

export const store = configureStore({
  reducer: {
    agents: agentsSlice,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;