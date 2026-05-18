'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { social } from '@/lib/api-client'
import { toast } from 'sonner'
import { formatDate } from '@/lib/utils'
import { CheckCircle, Clock, AlertCircle } from 'lucide-react'

const STATUS_ICONS: Record<string, any> = {
  pending_approval: Clock,
  scheduled: Clock,
  published: CheckCircle,
  failed: AlertCircle,
}
const STATUS_COLORS: Record<string, string> = {
  pending_approval: 'text-yellow-600 bg-yellow-50',
  scheduled: 'text-blue-600 bg-blue-50',
  published: 'text-green-600 bg-green-50',
  failed: 'text-red-600 bg-red-50',
}

export default function SocialPage() {
  const qc = useQueryClient()
  const { data, isLoading } = useQuery({ queryKey: ['social-posts'], queryFn: () => social.posts().then(r => r.data) })

  const approveMutation = useMutation({
    mutationFn: (id: string) => social.approvePost(id),
    onSuccess: () => { toast.success('Post approved and queued for publishing!'); qc.invalidateQueries({ queryKey: ['social-posts'] }) },
    onError: () => toast.error('Failed to approve post'),
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Social Media</h1>
        <p className="text-muted-foreground text-sm">AI-generated posts from your completed jobs</p>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-20"><div className="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full" /></div>
      ) : (
        <div className="grid gap-4">
          {data?.items?.length === 0 && (
            <div className="bg-white rounded-xl border border-border p-12 text-center text-gray-400">
              <p className="font-medium">No posts yet</p>
              <p className="text-sm mt-1">Complete a job in the pipeline to auto-generate your first post</p>
            </div>
          )}
          {data?.items?.map((post: any) => {
            const StatusIcon = STATUS_ICONS[post.status] || Clock
            return (
              <div key={post.id} className="bg-white rounded-xl border border-border p-5">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-xs font-medium bg-gray-100 text-muted-foreground px-2 py-0.5 rounded capitalize">{post.platform}</span>
                      <span className={`flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded ${STATUS_COLORS[post.status] || 'bg-gray-100 text-muted-foreground'}`}>
                        <StatusIcon className="w-3 h-3" />
                        {post.status.replace('_', ' ')}
                      </span>
                    </div>
                    <p className="text-sm text-foreground leading-relaxed">{post.content}</p>
                    <p className="text-xs text-gray-400 mt-3">{formatDate(post.created_at)}</p>
                  </div>
                  {post.status === 'pending_approval' && (
                    <button
                      onClick={() => approveMutation.mutate(post.id)}
                      disabled={approveMutation.isPending}
                      className="flex-shrink-0 bg-green-600 text-white text-xs px-4 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50"
                    >
                      Approve & Post
                    </button>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
