import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { KPICard } from '../../components/KPICard'
import { Briefcase, Building2, MapPin, Users } from 'lucide-react'

describe('KPICard', () => {
  it('renders title and value', () => {
    render(
      <KPICard title="Total Ofertas" value={16136} icon={Briefcase} color="blue" />
    )

    expect(screen.getByText('Total Ofertas')).toBeInTheDocument()
    // 16136 formatted with dot separator → "16.136"
    expect(screen.getByText('16.136')).toBeInTheDocument()
  })

  it('formats large numbers with dot separators', () => {
    render(
      <KPICard title="Test" value={1234567} icon={Briefcase} color="blue" />
    )

    expect(screen.getByText('1.234.567')).toBeInTheDocument()
  })

  it('renders string values as-is', () => {
    render(
      <KPICard title="Test" value="N/A" icon={Briefcase} color="blue" />
    )

    expect(screen.getByText('N/A')).toBeInTheDocument()
  })

  it('shows upward trend with positive change', () => {
    render(
      <KPICard title="Test" value={100} icon={Briefcase} color="blue" change={12} trend="up" />
    )

    expect(screen.getByText('+12% vs mes anterior')).toBeInTheDocument()
  })

  it('shows downward trend with negative change', () => {
    render(
      <KPICard title="Test" value={100} icon={Briefcase} color="blue" change={-5} trend="down" />
    )

    expect(screen.getByText('-5% vs mes anterior')).toBeInTheDocument()
  })

  it('hides trend when change is undefined', () => {
    render(
      <KPICard title="Test" value={100} icon={Briefcase} color="blue" />
    )

    expect(screen.queryByText(/vs mes anterior/)).not.toBeInTheDocument()
  })

  it('applies correct color classes', () => {
    const { container } = render(
      <KPICard title="Test" value={0} icon={Briefcase} color="green" />
    )

    const wrapper = container.firstChild as HTMLElement
    expect(wrapper.className).toContain('emerald')
  })

  it('renders different icons', () => {
    const icons = [
      { icon: Briefcase, label: 'briefcase' },
      { icon: Building2, label: 'building' },
      { icon: MapPin, label: 'map-pin' },
      { icon: Users, label: 'users' },
    ]

    icons.forEach(({ icon }) => {
      const { unmount } = render(
        <KPICard title="Test" value={0} icon={icon} color="blue" />
      )
      unmount()
    })
  })

  it('handles zero value', () => {
    render(
      <KPICard title="Test" value={0} icon={Briefcase} color="blue" />
    )

    expect(screen.getByText('0')).toBeInTheDocument()
  })
})
