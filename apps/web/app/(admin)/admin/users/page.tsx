'use client'

import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Search,
  ShieldCheck,
  AlertCircle,
  Mail,
  Plus,
  Edit2,
  Trash2,
  X,
  Users,
  Shield,
  Activity,
  CheckCircle2,
  MoreHorizontal,
} from 'lucide-react'
import { toast } from 'sonner'
import { admin, adminApi as adminPanel } from '@/lib/api-client'

// ─── types ────────────────────────────────────────────────────────────────────

interface AdminUser {
  id: string
  email: string
  full_name: string
  user_type?: string
  is_superadmin: boolean
  email_verified_at: string | null
  created_at: string
}

interface AdminRole {
  id: string
  name: string
  permissions: string[]
  description: string
}

interface ActivityLog {
  id: string
  user_id: string
  action: string
  resource_type: string | null
  resource_id: string | null
  ip_address: string | null
  created_at: string
}

type Tab = 'users' | 'roles' | 'activity'

// ─── helpers ──────────────────────────────────────────────────────────────────

function fmt(d: string | null) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

// ─── Modal shell ──────────────────────────────────────────────────────────────

function Modal({ title, onClose, children }: { title: string; onClose: () => void; children: React.ReactNode }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
      <div className="w-full max-w-lg rounded-2xl border border-gray-800 bg-gray-950 shadow-2xl">
        <div className="flex items-center justify-between border-b border-gray-800 px-6 py-4">
          <h3 className="text-base font-semibold text-white">{title}</h3>
          <button onClick={onClose} className="rounded-md p-1 text-gray-500 hover:bg-gray-800 hover:text-white">
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="p-6">{children}</div>
      </div>
    </div>
  )
}

// ─── Create User Modal ────────────────────────────────────────────────────────

function CreateUserModal({ onClose }: { onClose: () => void }) {
  const qc = useQueryClient()
  const [email, setEmail] = useState('')
  const [name, setName] = useState('')
  const [isSuperadmin, setIsSuperadmin] = useState(false)

  const create = useMutation({
    mutationFn: () => adminPanel.createAdminUser({ email, full_name: name, is_superadmin: isSuperadmin }),
    onSuccess: () => {
      toast.success('User created — they will receive a magic link to set their password.')
      qc.invalidateQueries({ queryKey: ['admin', 'users'] })
      onClose()
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail || 'Failed to create user'),
  })

  return (
    <Modal title="Create Admin User" onClose={onClose}>
      <div className="space-y-4">
        <div>
          <label className="mb-1.5 block text-xs font-medium text-gray-400">Full name</label>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Jane Smith"
            className="w-full rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-amber-500/40"
          />
        </div>
        <div>
          <label className="mb-1.5 block text-xs font-medium text-gray-400">Email address</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="jane@example.com"
            className="w-full rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-amber-500/40"
          />
        </div>
        <label className="flex cursor-pointer items-center gap-3">
          <div
            onClick={() => setIsSuperadmin((v) => !v)}
            className={`relative h-5 w-9 rounded-full transition-colors ${isSuperadmin ? 'bg-amber-500' : 'bg-gray-700'}`}
          >
            <span
              className={`absolute top-0.5 h-4 w-4 rounded-full bg-white transition-transform ${isSuperadmin ? 'translate-x-4' : 'translate-x-0.5'}`}
            />
          </div>
          <span className="text-sm text-gray-300">Grant super-admin privileges</span>
        </label>
        <div className="flex justify-end gap-3 pt-2">
          <button onClick={onClose} className="rounded-lg border border-gray-700 px-4 py-2 text-sm text-gray-300 hover:bg-gray-800">
            Cancel
          </button>
          <button
            disabled={!email || !name || create.isPending}
            onClick={() => create.mutate()}
            className="rounded-lg bg-amber-500 px-4 py-2 text-sm font-semibold text-black hover:bg-amber-400 disabled:opacity-50"
          >
            {create.isPending ? 'Creating…' : 'Create User'}
          </button>
        </div>
      </div>
    </Modal>
  )
}

// ─── Edit User Modal ──────────────────────────────────────────────────────────

function EditUserModal({ user, onClose }: { user: AdminUser; onClose: () => void }) {
  const qc = useQueryClient()
  const [name, setName] = useState(user.full_name)
  const [isSuperadmin, setIsSuperadmin] = useState(user.is_superadmin)

  const save = useMutation({
    mutationFn: () => adminPanel.updateAdminUser(user.id, { full_name: name, is_superadmin: isSuperadmin }),
    onSuccess: () => {
      toast.success('User updated')
      qc.invalidateQueries({ queryKey: ['admin', 'users'] })
      onClose()
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail || 'Update failed'),
  })

  return (
    <Modal title={`Edit — ${user.email}`} onClose={onClose}>
      <div className="space-y-4">
        <div>
          <label className="mb-1.5 block text-xs font-medium text-gray-400">Full name</label>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-amber-500/40"
          />
        </div>
        <label className="flex cursor-pointer items-center gap-3">
          <div
            onClick={() => setIsSuperadmin((v) => !v)}
            className={`relative h-5 w-9 rounded-full transition-colors ${isSuperadmin ? 'bg-amber-500' : 'bg-gray-700'}`}
          >
            <span className={`absolute top-0.5 h-4 w-4 rounded-full bg-white transition-transform ${isSuperadmin ? 'translate-x-4' : 'translate-x-0.5'}`} />
          </div>
          <span className="text-sm text-gray-300">Super-admin access</span>
        </label>
        <p className="rounded-lg border border-blue-500/20 bg-blue-500/5 p-3 text-xs text-blue-300">
          To reset a user&apos;s password, use the magic-link auth flow — send a login link from the Auth screen.
        </p>
        <div className="flex justify-end gap-3 pt-2">
          <button onClick={onClose} className="rounded-lg border border-gray-700 px-4 py-2 text-sm text-gray-300 hover:bg-gray-800">
            Cancel
          </button>
          <button
            disabled={save.isPending}
            onClick={() => save.mutate()}
            className="rounded-lg bg-amber-500 px-4 py-2 text-sm font-semibold text-black hover:bg-amber-400 disabled:opacity-50"
          >
            {save.isPending ? 'Saving…' : 'Save Changes'}
          </button>
        </div>
      </div>
    </Modal>
  )
}

// ─── Delete User Confirm ──────────────────────────────────────────────────────

function DeleteUserModal({ user, onClose }: { user: AdminUser; onClose: () => void }) {
  const qc = useQueryClient()
  const del = useMutation({
    mutationFn: () => admin.deleteUser(user.id),
    onSuccess: async () => {
      toast.success('User deleted')
      await qc.refetchQueries({ queryKey: ['admin', 'users'] })
      qc.invalidateQueries({ queryKey: ['admin', 'stats'] })
      onClose()
    },
    onError: (e: any) => {
      const detail = e?.response?.data?.detail
      const msg =
        typeof detail === 'string'
          ? detail
          : Array.isArray(detail)
            ? detail.map((d: { msg?: string }) => d?.msg).filter(Boolean).join('; ')
            : 'Delete failed'
      toast.error(msg || 'Delete failed')
    },
  })

  return (
    <Modal title="Delete User" onClose={onClose}>
      <div className="space-y-4">
        <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-4">
          <p className="text-sm text-red-300">
            Permanently delete <strong>{user.email}</strong>
            {user.user_type === 'freelancer' ? ' (freelancer)' : ''}?
            This removes the account, revokes access, and deletes owned workspace data. This cannot be undone.
          </p>
        </div>
        <div className="flex justify-end gap-3">
          <button onClick={onClose} className="rounded-lg border border-gray-700 px-4 py-2 text-sm text-gray-300 hover:bg-gray-800">
            Cancel
          </button>
          <button
            disabled={del.isPending}
            onClick={() => del.mutate()}
            className="rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-500 disabled:opacity-50"
          >
            {del.isPending ? 'Deleting…' : 'Yes, Delete User'}
          </button>
        </div>
      </div>
    </Modal>
  )
}

// ─── Role Modal ───────────────────────────────────────────────────────────────

const ALL_PERMISSIONS = [
  'tenants.read', 'tenants.write', 'tenants.delete',
  'users.read', 'users.write',
  'billing.read', 'billing.write',
  'content.read', 'content.write',
  'leads.read', 'leads.write',
  'scraper.read', 'scraper.write',
  'referrals.read', 'referrals.write',
  'support.read', 'support.write',
  'operations.read',
]

function RoleModal({ role, onClose }: { role?: AdminRole; onClose: () => void }) {
  const qc = useQueryClient()
  const [name, setName] = useState(role?.name ?? '')
  const [desc, setDesc] = useState(role?.description ?? '')
  const [perms, setPerms] = useState<Set<string>>(new Set(role?.permissions ?? []))

  function togglePerm(p: string) {
    setPerms((prev) => {
      const next = new Set(prev)
      if (next.has(p)) next.delete(p)
      else next.add(p)
      return next
    })
  }

  const save = useMutation({
    mutationFn: () => {
      const body = { name, description: desc, permissions: Array.from(perms) }
      return role
        ? adminPanel.updateRole(role.id, body)
        : adminPanel.createRole(body)
    },
    onSuccess: () => {
      toast.success(role ? 'Role updated' : 'Role created')
      qc.invalidateQueries({ queryKey: ['admin', 'roles'] })
      onClose()
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail || 'Failed'),
  })

  return (
    <Modal title={role ? `Edit Role — ${role.name}` : 'Create Role'} onClose={onClose}>
      <div className="space-y-4">
        <div>
          <label className="mb-1.5 block text-xs font-medium text-gray-400">Role name</label>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. Support Agent"
            className="w-full rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-amber-500/40"
          />
        </div>
        <div>
          <label className="mb-1.5 block text-xs font-medium text-gray-400">Description</label>
          <input
            value={desc}
            onChange={(e) => setDesc(e.target.value)}
            placeholder="What this role can do"
            className="w-full rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-amber-500/40"
          />
        </div>
        <div>
          <label className="mb-2 block text-xs font-medium text-gray-400">Permissions</label>
          <div className="grid grid-cols-2 gap-1.5">
            {ALL_PERMISSIONS.map((p) => (
              <label key={p} className="flex cursor-pointer items-center gap-2 rounded-lg border border-gray-800 px-3 py-2 hover:border-gray-700">
                <input
                  type="checkbox"
                  checked={perms.has(p)}
                  onChange={() => togglePerm(p)}
                  className="h-3.5 w-3.5 rounded accent-amber-500"
                />
                <span className="text-xs text-gray-300">{p}</span>
              </label>
            ))}
          </div>
        </div>
        <div className="flex justify-end gap-3 pt-2">
          <button onClick={onClose} className="rounded-lg border border-gray-700 px-4 py-2 text-sm text-gray-300 hover:bg-gray-800">
            Cancel
          </button>
          <button
            disabled={!name || save.isPending}
            onClick={() => save.mutate()}
            className="rounded-lg bg-amber-500 px-4 py-2 text-sm font-semibold text-black hover:bg-amber-400 disabled:opacity-50"
          >
            {save.isPending ? 'Saving…' : role ? 'Save Changes' : 'Create Role'}
          </button>
        </div>
      </div>
    </Modal>
  )
}

// ─── Users tab ────────────────────────────────────────────────────────────────

function UsersTab() {
  const [search, setSearch] = useState('')
  const [createOpen, setCreateOpen] = useState(false)
  const [editUser, setEditUser] = useState<AdminUser | null>(null)
  const [deleteUser, setDeleteUser] = useState<AdminUser | null>(null)

  const { data, isLoading, error } = useQuery<AdminUser[]>({
    queryKey: ['admin', 'users', search],
    queryFn: () => admin.listUsers({ q: search || undefined }).then((r) => r.data),
  })

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by email or name…"
            className="w-full rounded-lg border border-gray-800 bg-gray-900 pl-10 pr-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500/40"
          />
        </div>
        <button
          onClick={() => setCreateOpen(true)}
          className="inline-flex items-center gap-1.5 rounded-lg bg-amber-500 px-3 py-2 text-sm font-semibold text-black hover:bg-amber-400"
        >
          <Plus className="h-4 w-4" />
          New User
        </button>
      </div>

      {error && (
        <div className="flex items-center gap-3 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          <AlertCircle className="h-4 w-4 shrink-0" />
          Failed to load users.
        </div>
      )}

      <div className="space-y-3 md:hidden">
        {isLoading && [...Array(4)].map((_, i) => (
          <div key={i} className="h-28 animate-pulse rounded-xl border border-gray-800 bg-gray-900" />
        ))}
        {!isLoading && data?.length === 0 && (
          <div className="rounded-xl border border-dashed border-gray-700 py-12 text-center text-sm text-gray-500">
            No users found.
          </div>
        )}
        {data?.map((u) => (
          <article key={u.id} className="rounded-xl border border-gray-800 bg-gray-900/60 p-4">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <h3 className="truncate font-semibold text-gray-100">{u.full_name || '—'}</h3>
                <p className="mt-1 flex items-center gap-1.5 truncate text-xs text-gray-500">
                  <Mail className="h-3 w-3 shrink-0" /> {u.email}
                </p>
              </div>
              {u.is_superadmin ? (
                <span className="inline-flex shrink-0 items-center gap-1 rounded border border-amber-500/30 bg-amber-500/15 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-amber-300">
                  <ShieldCheck className="h-3 w-3" /> Super Admin
                </span>
              ) : (
                <span className="shrink-0 rounded border border-gray-700 px-2 py-0.5 text-[10px] uppercase text-gray-500">
                  {u.user_type === 'freelancer' ? 'Freelancer' : 'Tenant'}
                </span>
              )}
            </div>
            <div className="mt-3 grid grid-cols-2 gap-3 text-xs">
              <div>
                <p className="text-gray-500">Email verified</p>
                <p className={u.email_verified_at ? 'mt-0.5 text-emerald-400' : 'mt-0.5 text-gray-600'}>
                  {u.email_verified_at ? fmt(u.email_verified_at) : 'Unverified'}
                </p>
              </div>
              <div>
                <p className="text-gray-500">Joined</p>
                <p className="mt-0.5 text-gray-300">{fmt(u.created_at)}</p>
              </div>
            </div>
            <div className="mt-4 flex gap-2">
              <button
                onClick={() => setEditUser(u)}
                className="inline-flex flex-1 items-center justify-center gap-1.5 rounded-lg border border-gray-700 px-3 py-2 text-xs text-gray-300 hover:bg-gray-800 hover:text-white"
              >
                <Edit2 className="h-3.5 w-3.5" /> Edit
              </button>
              <button
                onClick={() => setDeleteUser(u)}
                disabled={u.is_superadmin}
                className="inline-flex flex-1 items-center justify-center gap-1.5 rounded-lg border border-red-900 px-3 py-2 text-xs text-red-400 hover:bg-red-950/40 disabled:opacity-40"
              >
                <Trash2 className="h-3.5 w-3.5" /> Delete
              </button>
            </div>
          </article>
        ))}
      </div>

      <div className="hidden overflow-x-auto rounded-xl border border-gray-800 md:block">
        <table className="min-w-[760px] w-full text-sm">
          <thead className="bg-gray-950 text-xs uppercase tracking-wider text-gray-500">
            <tr>
              <th className="px-5 py-3 text-left font-semibold">User</th>
              <th className="px-5 py-3 text-left font-semibold">Role</th>
              <th className="px-5 py-3 text-left font-semibold">Email verified</th>
              <th className="px-5 py-3 text-right font-semibold">Joined</th>
              <th className="px-5 py-3 text-right font-semibold">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800">
            {isLoading && [...Array(4)].map((_, i) => (
              <tr key={i}><td colSpan={5} className="px-5 py-4"><div className="h-6 animate-pulse rounded bg-gray-800" /></td></tr>
            ))}
            {!isLoading && data?.length === 0 && (
              <tr><td colSpan={5} className="px-5 py-12 text-center text-gray-500">No users found.</td></tr>
            )}
            {data?.map((u) => (
              <tr key={u.id} className="group hover:bg-gray-800/20">
                <td className="px-5 py-3">
                  <div className="font-medium text-gray-100">{u.full_name || '—'}</div>
                  <div className="flex items-center gap-1.5 text-xs text-gray-500">
                    <Mail className="h-3 w-3" /> {u.email}
                  </div>
                </td>
                <td className="px-5 py-3">
                  {u.is_superadmin ? (
                    <span className="inline-flex items-center gap-1 rounded border border-amber-500/30 bg-amber-500/15 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-amber-300">
                      <ShieldCheck className="h-3 w-3" /> Super Admin
                    </span>
                  ) : (
                    <span className="text-xs capitalize text-gray-500">
                      {u.user_type === 'freelancer' ? 'Freelancer' : 'Tenant'}
                    </span>
                  )}
                </td>
                <td className="px-5 py-3 text-xs text-gray-400">
                  {u.email_verified_at ? (
                    <span className="flex items-center gap-1 text-emerald-400">
                      <CheckCircle2 className="h-3 w-3" /> {fmt(u.email_verified_at)}
                    </span>
                  ) : (
                    <span className="text-gray-600">Unverified</span>
                  )}
                </td>
                <td className="px-5 py-3 text-right text-xs text-gray-400">{fmt(u.created_at)}</td>
                <td className="px-5 py-3 text-right">
                  <div className="flex items-center justify-end gap-1">
                    <button
                      onClick={() => setEditUser(u)}
                      className="rounded p-1.5 text-gray-400 hover:bg-gray-700 hover:text-white"
                      title="Edit"
                    >
                      <Edit2 className="h-3.5 w-3.5" />
                    </button>
                    <button
                      onClick={() => setDeleteUser(u)}
                      disabled={u.is_superadmin}
                      className="rounded p-1.5 text-gray-400 hover:bg-red-500/10 hover:text-red-400 disabled:opacity-40"
                      title="Delete"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {createOpen && <CreateUserModal onClose={() => setCreateOpen(false)} />}
      {editUser && <EditUserModal user={editUser} onClose={() => setEditUser(null)} />}
      {deleteUser && <DeleteUserModal user={deleteUser} onClose={() => setDeleteUser(null)} />}
    </div>
  )
}

// ─── Roles tab ────────────────────────────────────────────────────────────────

function RolesTab() {
  const [createOpen, setCreateOpen] = useState(false)
  const [editRole, setEditRole] = useState<AdminRole | null>(null)
  const qc = useQueryClient()

  const { data, isLoading, error } = useQuery<AdminRole[]>({
    queryKey: ['admin', 'roles'],
    queryFn: () => adminPanel.listRoles().then((r) => r.data),
  })

  const del = useMutation({
    mutationFn: (id: string) => adminPanel.deleteRole(id),
    onSuccess: () => {
      toast.success('Role deleted')
      qc.invalidateQueries({ queryKey: ['admin', 'roles'] })
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail || 'Failed'),
  })

  return (
    <div className="space-y-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-sm text-gray-400">Define permission scopes for sub-admin users.</p>
        <button
          onClick={() => setCreateOpen(true)}
          className="inline-flex items-center gap-1.5 rounded-lg bg-amber-500 px-3 py-2 text-sm font-semibold text-black hover:bg-amber-400"
        >
          <Plus className="h-4 w-4" />
          New Role
        </button>
      </div>

      {error && (
        <div className="flex items-center gap-3 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          <AlertCircle className="h-4 w-4 shrink-0" />
          Failed to load roles. The admin_roles table may not exist yet — run migrations.
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        {isLoading && [0, 1, 2].map((i) => (
          <div key={i} className="h-32 animate-pulse rounded-xl border border-gray-800 bg-gray-900" />
        ))}
        {!isLoading && data?.length === 0 && (
          <div className="col-span-2 rounded-xl border border-dashed border-gray-700 py-12 text-center text-sm text-gray-500">
            No roles yet.{' '}
            <button onClick={() => setCreateOpen(true)} className="text-amber-400 underline hover:text-amber-300">
              Create the first role
            </button>
          </div>
        )}
        {data?.map((role) => (
          <div key={role.id} className="group relative rounded-xl border border-gray-800 bg-gray-900/50 p-5">
            <div className="mb-3 flex items-start justify-between">
              <div>
                <p className="font-semibold text-white">{role.name}</p>
                <p className="text-xs text-gray-500">{role.description || 'No description'}</p>
              </div>
              <div className="flex gap-1 opacity-100 transition-opacity sm:opacity-0 sm:group-hover:opacity-100">
                <button
                  onClick={() => setEditRole(role)}
                  className="rounded p-1.5 text-gray-400 hover:bg-gray-700 hover:text-white"
                >
                  <Edit2 className="h-3.5 w-3.5" />
                </button>
                <button
                  onClick={() => del.mutate(role.id)}
                  disabled={del.isPending}
                  className="rounded p-1.5 text-gray-400 hover:bg-red-500/10 hover:text-red-400 disabled:opacity-40"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
            <div className="flex flex-wrap gap-1">
              {role.permissions.length === 0 ? (
                <span className="text-xs text-gray-600">No permissions assigned</span>
              ) : (
                role.permissions.slice(0, 8).map((p) => (
                  <span key={p} className="rounded border border-gray-700 px-1.5 py-0.5 text-[10px] text-gray-400">
                    {p}
                  </span>
                ))
              )}
              {role.permissions.length > 8 && (
                <span className="text-xs text-gray-600">+{role.permissions.length - 8} more</span>
              )}
            </div>
          </div>
        ))}
      </div>

      {createOpen && <RoleModal onClose={() => setCreateOpen(false)} />}
      {editRole && <RoleModal role={editRole} onClose={() => setEditRole(null)} />}
    </div>
  )
}

// ─── Activity tab ─────────────────────────────────────────────────────────────

function ActivityTab() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['admin', 'activity'],
    queryFn: () => adminPanel.listActivityLogs({ limit: 200 }).then((r) => r.data),
  })

  return (
    <div className="space-y-4">
      {error && (
        <div className="flex items-center gap-3 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          <AlertCircle className="h-4 w-4 shrink-0" />
          Failed to load activity logs.
        </div>
      )}
      <div className="overflow-x-auto rounded-xl border border-gray-800">
        <table className="min-w-[820px] w-full text-sm">
          <thead className="bg-gray-950 text-xs uppercase tracking-wider text-gray-500">
            <tr>
              <th className="px-5 py-3 text-left font-semibold">User</th>
              <th className="px-5 py-3 text-left font-semibold">Action</th>
              <th className="px-5 py-3 text-left font-semibold">Resource</th>
              <th className="px-5 py-3 text-left font-semibold">IP</th>
              <th className="px-5 py-3 text-right font-semibold">When</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800">
            {isLoading && [...Array(4)].map((_, i) => (
              <tr key={i}><td colSpan={5} className="px-5 py-4"><div className="h-5 animate-pulse rounded bg-gray-800" /></td></tr>
            ))}
            {!isLoading && (data as ActivityLog[] | undefined)?.length === 0 && (
              <tr><td colSpan={5} className="px-5 py-12 text-center text-gray-500">No activity logs yet.</td></tr>
            )}
            {(data as ActivityLog[] | undefined)?.map((l) => (
              <tr key={l.id} className="hover:bg-gray-800/20">
                <td className="px-5 py-3 font-mono text-xs text-gray-400">{l.user_id.slice(0, 8)}…</td>
                <td className="px-5 py-3">
                  <span className="rounded border border-gray-700 px-2 py-0.5 text-xs text-gray-300">{l.action}</span>
                </td>
                <td className="px-5 py-3 text-xs text-gray-400">
                  {l.resource_type ? `${l.resource_type} ${l.resource_id?.slice(0, 8) ?? ''}` : '—'}
                </td>
                <td className="px-5 py-3 text-xs text-gray-500">{l.ip_address || '—'}</td>
                <td className="px-5 py-3 text-right text-xs text-gray-400">{fmt(l.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ─── Main page ────────────────────────────────────────────────────────────────

export default function AdminUsersPage() {
  const [tab, setTab] = useState<Tab>('users')

  const tabs: { id: Tab; label: string; icon: React.ElementType }[] = [
    { id: 'users', label: 'Users', icon: Users },
    { id: 'roles', label: 'Roles & Permissions', icon: Shield },
    { id: 'activity', label: 'Activity Log', icon: Activity },
  ]

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-bold tracking-tight">Users &amp; Roles</h1>
        <p className="mt-1 text-gray-400">
          Manage platform users, define permission roles, and review admin activity.
        </p>
      </header>

      {/* Tab nav */}
      <div className="flex gap-1 overflow-x-auto rounded-xl border border-gray-800 bg-gray-900 p-1">
        {tabs.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setTab(id)}
            className={`flex items-center gap-2 whitespace-nowrap rounded-lg px-4 py-2 text-sm font-semibold transition-colors ${
              tab === id ? 'bg-amber-500/15 text-amber-300' : 'text-gray-400 hover:bg-gray-800 hover:text-white'
            }`}
          >
            <Icon className="h-4 w-4" />
            {label}
          </button>
        ))}
      </div>

      {tab === 'users' && <UsersTab />}
      {tab === 'roles' && <RolesTab />}
      {tab === 'activity' && <ActivityTab />}
    </div>
  )
}
