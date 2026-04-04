import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { usersApi } from '@/api/users'
import { useUserStore } from '@/store/userStore'

export function useUserProfile(userId: string | null, enabled = true) {
  return useQuery({
    queryKey: ['user', userId],
    queryFn: async () => {
      if (!userId) throw new Error('No user ID')
      return usersApi.getProfile(userId)
    },
    enabled: enabled && !!userId,
    staleTime: 1000 * 60 * 5, // 5 minutes
  })
}

export function useOnboarding() {
  const queryClient = useQueryClient()
  const { setUser } = useUserStore()

  return useMutation({
    mutationFn: (data: Parameters<typeof usersApi.onboard>[0]) =>
      usersApi.onboard(data),
    onSuccess: (user: any) => {
      setUser(user.id, user.name, user.email)
      queryClient.setQueryData(['user', user.id], user)
    },
  })
}

export function useUpdateStaples(userId: string | null) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (staples: any[]) => {
      if (!userId) throw new Error('No user ID')
      return usersApi.updateStaples(userId, staples)
    },
    onSuccess: (user: any) => {
      queryClient.setQueryData(['user', userId], user)
    },
  })
}
