import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { IngredientCollectionPage } from './pages';

/**
 * Create React Query client
 * Configuration for caching and refetching behavior
 */
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

/**
 * Main App Component
 *
 * Sets up React Query provider and renders the main page.
 */
function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <IngredientCollectionPage />
    </QueryClientProvider>
  );
}

export default App;
