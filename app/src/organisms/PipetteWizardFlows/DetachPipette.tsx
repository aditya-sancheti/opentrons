import * as React from 'react'
import capitalize from 'lodash/capitalize'
import { useTranslation } from 'react-i18next'
import { SIZE_1 } from '@opentrons/components'
import { WEIGHT_OF_96_CHANNEL } from '@opentrons/shared-data'
import { StyledText } from '../../atoms/text'
import { GenericWizardTile } from '../../molecules/GenericWizardTile'
import { Skeleton } from '../../atoms/Skeleton'
import { Banner } from '../../atoms/Banner'
import { InProgressModal } from '../../molecules/InProgressModal/InProgressModal'
import detachPipette from '../../assets/images/change-pip/single-channel-detach-pipette.png'
import detach96Pipette from '../../assets/images/change-pip/detach-96-pipette.png'
import { CheckPipetteButton } from './CheckPipetteButton'
import { BODY_STYLE } from './constants'
import type { PipetteWizardStepProps } from './types'

interface DetachPipetteProps extends PipetteWizardStepProps {
  isFetching: boolean
  setFetching: React.Dispatch<React.SetStateAction<boolean>>
}
const BACKGROUND_SIZE = '47rem'

export const DetachPipette = (props: DetachPipetteProps): JSX.Element => {
  const {
    isRobotMoving,
    goBack,
    proceed,
    attachedPipettes,
    mount,
    isFetching,
    setFetching,
    isOnDevice,
  } = props
  const { t } = useTranslation(['pipette_wizard_flows', 'shared'])
  const is96ChannelPipette = attachedPipettes[mount]?.name === 'p1000_96'

  let bodyText: React.ReactNode = <div></div>
  if (isFetching) {
    bodyText = (
      <>
        <Skeleton
          width="18rem"
          height="1.125rem"
          backgroundSize={BACKGROUND_SIZE}
        />
        <Skeleton
          width="18rem"
          height="1.125rem"
          backgroundSize={BACKGROUND_SIZE}
        />
      </>
    )
  } else {
    bodyText = (
      <>
        <StyledText css={BODY_STYLE}>{t('hold_and_loosen')}</StyledText>
        {!is96ChannelPipette ? null : (
          <Banner type="warning" size={isOnDevice ? '1.5rem' : SIZE_1}>
            {t('pipette_heavy', { weight: WEIGHT_OF_96_CHANNEL })}
          </Banner>
        )}
      </>
    )
  }

  if (isRobotMoving) return <InProgressModal description={t('stand_back')} />
  return (
    <GenericWizardTile
      header={
        isFetching ? (
          <Skeleton
            width="17rem"
            height="1.75rem"
            backgroundSize={BACKGROUND_SIZE}
          />
        ) : !is96ChannelPipette ? (
          t('loose_detach', {
            pipetteName: attachedPipettes[mount]?.modelSpecs.displayName,
          })
        ) : (
          t('unscrew_remove_96_channel')
        )
      }
      //  TODO(Jr, 11/8/22): replace image with correct one!
      rightHandBody={
        isFetching ? (
          <Skeleton
            width="100%"
            height="14.375rem"
            backgroundSize={BACKGROUND_SIZE}
          />
        ) : (
          <img
            src={!is96ChannelPipette ? detachPipette : detach96Pipette}
            width="100%"
            alt={
              !is96ChannelPipette
                ? 'Detach pipette'
                : 'Unscrew 96 channel pipette'
            }
          />
        )
      }
      bodyText={bodyText}
      backIsDisabled={isFetching}
      back={goBack}
      proceedButton={
        <CheckPipetteButton
          isOnDevice={isOnDevice}
          proceedButtonText={capitalize(t('shared:continue'))}
          proceed={proceed}
          setFetching={setFetching}
          isFetching={isFetching}
        />
      }
    />
  )
}
