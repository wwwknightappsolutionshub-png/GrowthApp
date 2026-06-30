import type { BlogPost } from '@/lib/blog'
import { canonical, SITE_URL } from '@/lib/seo'

export function BlogPostJsonLd({ post }: { post: BlogPost }) {
  const url = canonical(`/blog/${post.slug}`)
  const schema = {
    '@context': 'https://schema.org',
    '@type': 'BlogPosting',
    headline: post.title,
    description: post.excerpt ?? post.seo_description ?? undefined,
    image: post.image_url ? [post.image_url] : [`${SITE_URL}/opengraph-image`],
    datePublished: post.published_at ?? undefined,
    dateModified: post.updated_at ?? post.published_at ?? undefined,
    author: {
      '@type': 'Person',
      name: post.author_name ?? 'CustomerFlow Team',
    },
    publisher: {
      '@type': 'Organization',
      name: 'CustomerFlowai',
      logo: {
        '@type': 'ImageObject',
        url: `${SITE_URL}/icons/icon.svg`,
      },
    },
    mainEntityOfPage: {
      '@type': 'WebPage',
      '@id': url,
    },
    url,
  }

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
    />
  )
}
