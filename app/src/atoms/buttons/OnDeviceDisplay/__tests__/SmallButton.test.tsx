import * as React from 'react'
import { renderWithProviders, COLORS, BORDERS } from '@opentrons/components'

import { SmallButton } from '../SmallButton'

const render = (props: React.ComponentProps<typeof SmallButton>) => {
  return renderWithProviders(<SmallButton {...props} />)[0]
}

describe('SmallButton', () => {
  let props: React.ComponentProps<typeof SmallButton>

  beforeEach(() => {
    props = {
      onClick: jest.fn(),
      buttonType: 'default',
      buttonText: 'small button',
    }
  })
  it('renders the default button and it works as expected', () => {
    const { getByText, getByRole } = render(props)
    getByText('small button').click()
    expect(props.onClick).toHaveBeenCalled()
    expect(getByRole('button')).toHaveStyle(
      `background-color: ${COLORS.blueEnabled}`
    )
    expect(getByRole('button')).toHaveStyle(
      `border-radius: ${BORDERS.size_four}`
    )
  })
  it('renders the alert button', () => {
    props = {
      ...props,
      buttonType: 'alert',
    }
    const { getByRole } = render(props)
    expect(getByRole('button')).toHaveStyle(
      `background-color: ${COLORS.red_two}`
    )
  })
  it('renders the alt button', () => {
    props = {
      ...props,
      buttonType: 'alt',
    }
    const { getByRole } = render(props)
    expect(getByRole('button')).toHaveStyle(
      `background-color: ${COLORS.foundationalBlue}`
    )
  })
  it('renders the tertiary high light button', () => {
    props = {
      ...props,
      buttonType: 'tertiaryHighLight',
    }
    const { getByRole } = render(props)
    expect(getByRole('button')).toHaveStyle(
      `color: ${COLORS.darkBlackEnabled}${COLORS.opacity70HexCode}`
    )
  })
  it('renders the tertiary low light', () => {
    props = {
      ...props,
      buttonType: 'tertiaryLowLight',
    }
    const { getByRole } = render(props)
    expect(getByRole('button')).toHaveStyle(`color: ${COLORS.darkBlackEnabled}`)
  })
  it('renders the button as disabled', () => {
    props = {
      ...props,
      disabled: true,
    }
    const { getByRole } = render(props)
    expect(getByRole('button')).toBeDisabled()
  })
  it('renders the rounded button category', () => {
    props = {
      ...props,
      buttonCategory: 'rounded',
    }
    const { getByRole } = render(props)
    expect(getByRole('button')).toHaveStyle(
      `border-radius: ${BORDERS.size_five}`
    )
  })
  it('renders an icon with start placement', () => {
    props = {
      ...props,
      iconName: 'alert',
      iconPlacement: 'startIcon',
    }
    const { getByLabelText } = render(props)
    getByLabelText('SmallButton_alert_positionStart')
  })
  it('renders an icon with end placement', () => {
    props = {
      ...props,
      iconName: 'alert',
      iconPlacement: 'endIcon',
    }
    const { getByLabelText } = render(props)
    getByLabelText('SmallButton_alert_positionEnd')
  })
})
