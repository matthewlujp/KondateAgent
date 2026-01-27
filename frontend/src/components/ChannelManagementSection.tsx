import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { creatorsApi } from '../api/creators';
import { detectSource } from '../utils/detectSource';
import { AddChannelInput } from './AddChannelInput';
import { ChannelCard } from './ChannelCard';
import type { PreferredCreator } from '../types';

export function ChannelManagementSection() {
  const queryClient = useQueryClient();
  const [addError, setAddError] = useState<string | null>(null);

  const { data: creators = [], isLoading: isLoadingList } = useQuery({
    queryKey: ['creators'],
    queryFn: creatorsApi.getCreators,
  });

  const addMutation = useMutation({
    mutationFn: creatorsApi.addCreator,
    onSuccess: (newCreator) => {
      queryClient.setQueryData<PreferredCreator[]>(['creators'], (old = []) => [
        newCreator,
        ...old,
      ]);
      setAddError(null);
    },
    onError: (error: any) => {
      const status = error.response?.status;
      if (status === 400) {
        setAddError('Invalid URL format. Please enter a valid YouTube or Instagram link.');
      } else if (status === 404) {
        setAddError('Channel not found. Please check the URL and try again.');
      } else {
        setAddError('Something went wrong. Please try again.');
      }
    },
  });

  const deleteMutation = useMutation({
    mutationFn: creatorsApi.deleteCreator,
    onMutate: async (creatorId) => {
      await queryClient.cancelQueries({ queryKey: ['creators'] });
      const previous = queryClient.getQueryData<PreferredCreator[]>(['creators']);
      queryClient.setQueryData<PreferredCreator[]>(['creators'], (old = []) =>
        old.filter((c) => c.id !== creatorId)
      );
      return { previous };
    },
    onError: (_err, _id, context) => {
      if (context?.previous) {
        queryClient.setQueryData(['creators'], context.previous);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['creators'] });
    },
  });

  const handleAdd = (url: string) => {
    const source = detectSource(url);
    if (!source) {
      setAddError('Please enter a valid YouTube or Instagram URL.');
      return;
    }
    setAddError(null);
    addMutation.mutate({ source, url });
  };

  const handleDelete = (id: string) => {
    deleteMutation.mutate(id);
  };

  return (
    <section className="bg-sand-50 border border-sand-200 rounded-xl shadow-warm p-6">
      <h2 className="text-lg font-semibold text-sand-900 mb-4">Favorite Channels</h2>

      <AddChannelInput
        onAdd={handleAdd}
        isLoading={addMutation.isPending}
        error={addError}
      />

      <div className="mt-4 space-y-2">
        {isLoadingList ? (
          // Skeleton loading state
          <>
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-16 bg-sand-100 rounded-lg animate-pulse" />
            ))}
          </>
        ) : creators.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-3xl mb-2">📺</div>
            <p className="font-medium text-sand-700">No channels yet</p>
            <p className="text-sm text-sand-500 mt-1">
              Add your first channel to get personalized recipe recommendations
            </p>
          </div>
        ) : (
          creators.map((creator) => (
            <ChannelCard
              key={creator.id}
              channel={creator}
              onDelete={handleDelete}
            />
          ))
        )}
      </div>
    </section>
  );
}
