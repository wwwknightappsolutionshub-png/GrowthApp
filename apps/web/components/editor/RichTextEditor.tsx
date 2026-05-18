'use client'

import { useEditor, EditorContent, type Editor } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Link from '@tiptap/extension-link'
import Placeholder from '@tiptap/extension-placeholder'
import {
  Bold,
  Italic,
  Strikethrough,
  Heading2,
  Heading3,
  List,
  ListOrdered,
  Quote,
  Undo2,
  Redo2,
  Link as LinkIcon,
  Unlink,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

interface RichTextEditorProps {
  value: string
  onChange: (html: string) => void
  placeholder?: string
  className?: string
  /** Show a slim toolbar (default true). */
  toolbar?: boolean
  /** Used by Outreach / SMS-like channels where rich formatting is overkill. */
  plain?: boolean
}

/**
 * Tenant-friendly TipTap wrapper. Outputs HTML by default (suitable for emails
 * and templates). For SMS-style channels, pass `plain` to strip formatting on
 * change.
 */
export function RichTextEditor({
  value,
  onChange,
  placeholder = 'Start typing...',
  className,
  toolbar = true,
  plain = false,
}: RichTextEditorProps) {
  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        heading: plain ? false : { levels: [2, 3] },
        codeBlock: plain ? false : undefined,
        blockquote: plain ? false : undefined,
        horizontalRule: plain ? false : undefined,
      }),
      Link.configure({
        openOnClick: false,
        autolink: true,
        HTMLAttributes: { rel: 'noopener noreferrer nofollow' },
      }),
      Placeholder.configure({ placeholder }),
    ],
    content: value,
    onUpdate({ editor }) {
      const html = editor.getHTML()
      const text = editor.getText()
      onChange(plain ? text : html)
    },
    editorProps: {
      attributes: {
        class: cn(
          'tiptap rounded-b-md border border-t-0 border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
          !toolbar && 'rounded-md border-t',
          className,
        ),
      },
    },
    immediatelyRender: false,
  })

  if (!editor) {
    return (
      <div className="rounded-md border border-input bg-background min-h-[180px]" />
    )
  }

  return (
    <div className="rounded-md">
      {toolbar && <Toolbar editor={editor} plain={plain} />}
      <EditorContent editor={editor} />
    </div>
  )
}

function Toolbar({ editor, plain }: { editor: Editor; plain: boolean }) {
  return (
    <div className="flex flex-wrap items-center gap-0.5 rounded-t-md border border-b-0 border-input bg-muted/50 px-1.5 py-1">
      <ToolbarBtn
        icon={<Bold className="h-3.5 w-3.5" />}
        onClick={() => editor.chain().focus().toggleBold().run()}
        active={editor.isActive('bold')}
        label="Bold"
      />
      <ToolbarBtn
        icon={<Italic className="h-3.5 w-3.5" />}
        onClick={() => editor.chain().focus().toggleItalic().run()}
        active={editor.isActive('italic')}
        label="Italic"
      />
      <ToolbarBtn
        icon={<Strikethrough className="h-3.5 w-3.5" />}
        onClick={() => editor.chain().focus().toggleStrike().run()}
        active={editor.isActive('strike')}
        label="Strike"
      />
      {!plain && (
        <>
          <ToolbarSeparator />
          <ToolbarBtn
            icon={<Heading2 className="h-3.5 w-3.5" />}
            onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
            active={editor.isActive('heading', { level: 2 })}
            label="Heading 2"
          />
          <ToolbarBtn
            icon={<Heading3 className="h-3.5 w-3.5" />}
            onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}
            active={editor.isActive('heading', { level: 3 })}
            label="Heading 3"
          />
          <ToolbarBtn
            icon={<Quote className="h-3.5 w-3.5" />}
            onClick={() => editor.chain().focus().toggleBlockquote().run()}
            active={editor.isActive('blockquote')}
            label="Quote"
          />
        </>
      )}
      <ToolbarSeparator />
      <ToolbarBtn
        icon={<List className="h-3.5 w-3.5" />}
        onClick={() => editor.chain().focus().toggleBulletList().run()}
        active={editor.isActive('bulletList')}
        label="Bullet list"
      />
      <ToolbarBtn
        icon={<ListOrdered className="h-3.5 w-3.5" />}
        onClick={() => editor.chain().focus().toggleOrderedList().run()}
        active={editor.isActive('orderedList')}
        label="Ordered list"
      />
      {!plain && (
        <>
          <ToolbarSeparator />
          <ToolbarBtn
            icon={<LinkIcon className="h-3.5 w-3.5" />}
            onClick={() => {
              const previousUrl = editor.getAttributes('link').href as string | undefined
              const url = window.prompt('URL', previousUrl || 'https://')
              if (url === null) return
              if (url === '') {
                editor.chain().focus().extendMarkRange('link').unsetLink().run()
                return
              }
              editor.chain().focus().extendMarkRange('link').setLink({ href: url }).run()
            }}
            active={editor.isActive('link')}
            label="Insert link"
          />
          <ToolbarBtn
            icon={<Unlink className="h-3.5 w-3.5" />}
            onClick={() => editor.chain().focus().unsetLink().run()}
            disabled={!editor.isActive('link')}
            label="Remove link"
          />
        </>
      )}
      <ToolbarSeparator />
      <ToolbarBtn
        icon={<Undo2 className="h-3.5 w-3.5" />}
        onClick={() => editor.chain().focus().undo().run()}
        disabled={!editor.can().undo()}
        label="Undo"
      />
      <ToolbarBtn
        icon={<Redo2 className="h-3.5 w-3.5" />}
        onClick={() => editor.chain().focus().redo().run()}
        disabled={!editor.can().redo()}
        label="Redo"
      />
    </div>
  )
}

function ToolbarBtn({
  icon,
  onClick,
  active,
  disabled,
  label,
}: {
  icon: React.ReactNode
  onClick: () => void
  active?: boolean
  disabled?: boolean
  label: string
}) {
  return (
    <Button
      type="button"
      variant="ghost"
      size="icon"
      onClick={onClick}
      disabled={disabled}
      title={label}
      aria-label={label}
      className={cn('h-7 w-7', active && 'bg-accent text-accent-foreground')}
    >
      {icon}
    </Button>
  )
}

function ToolbarSeparator() {
  return <div className="mx-1 h-4 w-px bg-border" />
}
