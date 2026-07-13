import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { Loading } from './Loading'

describe('Loading Component', () => {
  it('renders with the default message', () => {
    render(<Loading />)

    // Check if default text is present
    expect(screen.getByText('Loading...')).toBeInTheDocument()

    // Verify the element containing the class animate-spin (Loader2 icon)
    // The Loader2 SVG is rendered within the component.
    // We can query it by looking for the icon class or checking if the svg exists.
    const spinner = document.querySelector('.animate-spin')
    expect(spinner).toBeInTheDocument()
  })

  it('renders with a custom message', () => {
    const customMessage = "Fetching data..."
    render(<Loading message={customMessage} />)

    expect(screen.getByText(customMessage)).toBeInTheDocument()
    // Default message should not be there
    expect(screen.queryByText('Loading...')).not.toBeInTheDocument()
  })
})
