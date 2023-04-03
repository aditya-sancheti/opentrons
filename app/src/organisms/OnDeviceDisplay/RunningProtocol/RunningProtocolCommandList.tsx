import * as React from 'react'
import { useTranslation } from 'react-i18next'
import { css } from 'styled-components'
import { ViewportList, ViewportListRef } from 'react-viewport-list'

import {
  Flex,
  DIRECTION_ROW,
  COLORS,
  SPACING,
  Icon,
  DIRECTION_COLUMN,
  TYPOGRAPHY,
  JUSTIFY_SPACE_BETWEEN,
  Btn,
  ALIGN_CENTER,
  JUSTIFY_CENTER,
  DISPLAY_FLEX,
  BORDERS,
} from '@opentrons/components'
import { RUN_STATUS_RUNNING, RUN_STATUS_IDLE } from '@opentrons/api-client'

import { StyledText } from '../../../atoms/text'
import { CommandText } from '../../CommandText'
import { CommandIcon } from '../../RunPreview/CommandIcon'
import { SmallStopButton, SmallPlayPauseButton } from './Buttons'

import type { CompletedProtocolAnalysis } from '@opentrons/shared-data'
import type { RunStatus } from '@opentrons/api-client'
import type { TrackProtocolRunEvent } from '../../Devices/hooks'

const TITLE_TEXT_STYLE = css`
  color: ${COLORS.darkBlack_seventy};
  font-size: 1.75rem;
  font-weight: ${TYPOGRAPHY.fontWeightSemiBold};
  line-height: 2.25rem;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
`

const COMMAND_ROW_STYLE = css`
  font-size: 1.375rem;
  line-height: 1.75rem;
  font-weight: ${TYPOGRAPHY.fontWeightRegular}
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
`

interface RunningProtocolCommandListProps {
  runId: string
  runStatus: RunStatus | null
  robotSideAnalysis: CompletedProtocolAnalysis | null
  playRun: () => void
  pauseRun: () => void
  stopRun: () => void
  trackProtocolRunEvent: TrackProtocolRunEvent
  protocolName?: string
  currentRunCommandIndex?: number
}

export function RunningProtocolCommandList({
  runId, // may not need
  runStatus,
  robotSideAnalysis,
  playRun,
  pauseRun,
  stopRun,
  trackProtocolRunEvent,
  protocolName,
  currentRunCommandIndex,
}: RunningProtocolCommandListProps): JSX.Element {
  const { t } = useTranslation('run_details')
  const viewPortRef = React.useRef<HTMLDivElement | null>(null)
  const ref = React.useRef<ViewportListRef>(null)
  const currentRunStatus = t(`status_${runStatus}`)

  const onStop = (): void => {
    stopRun()
    // ToDo (kj:03/28/2023) update event information
    trackProtocolRunEvent({ name: 'runCancel', properties: { tbd: 'tbd' } })
  }

  const onTogglePlayPause = (): void => {
    if (runStatus === RUN_STATUS_RUNNING) {
      console.log('pause')
      pauseRun()
      // ToDo (kj:03/28/2023) update event information
      trackProtocolRunEvent({ name: 'runPause' })
    } else {
      console.log('playRun')
      playRun()
      // ToDo (kj:03/28/2023) update event information
      // trackProtocolRunEvent({
      //   name: runStatus === RUN_STATUS_IDLE ? 'runStart' : 'runResume',
      //   properties:
      //     runStatus === RUN_STATUS_IDLE && robotAnalyticsData != null
      //       ? robotAnalyticsData
      //       : {},
      // })
    }
  }

  return (
    <Flex flexDirection={DIRECTION_COLUMN} gridGap={SPACING.spacingXXL}>
      <Flex
        flexDirection={DIRECTION_ROW}
        justifyContent={JUSTIFY_SPACE_BETWEEN}
        gridGap={SPACING.spacingXXL}
      >
        <Flex flexDirection={DIRECTION_COLUMN} gridGap="0.25rem">
          <StyledText fontSize="1.75rem" lineHeight="2.25rem" fontWeight="700">
            {currentRunStatus}
          </StyledText>
          <StyledText css={TITLE_TEXT_STYLE}>{protocolName}</StyledText>
        </Flex>
        <Flex gridGap="1.5rem">
          <SmallStopButton onStop={onStop} />
          <SmallPlayPauseButton
            onTogglePlayPause={onTogglePlayPause}
            runStatus={runStatus}
          />
        </Flex>
      </Flex>
      {robotSideAnalysis != null ? (
        <Flex
          ref={viewPortRef}
          flexDirection={DIRECTION_COLUMN}
          gridGap={SPACING.spacing3}
        >
          <ViewportList
            viewportRef={viewPortRef}
            ref={ref}
            items={robotSideAnalysis?.commands}
            initialIndex={currentRunCommandIndex}
            // initialIndex={0}
          >
            {(command, index) => {
              const backgroundColor =
                index === currentRunCommandIndex
                  ? COLORS.foundationalBlue
                  : COLORS.light_one
              return (
                <Flex
                  key={command.id}
                  alignItems={ALIGN_CENTER}
                  gridGap={SPACING.spacing3}
                >
                  <Flex
                    padding={`0.75rem ${SPACING.spacing5}`}
                    alignItems={ALIGN_CENTER}
                    backgroundColor={backgroundColor}
                    width="100%"
                    fontSize="1.375rem"
                    lineHeight="1.75rem"
                    fontWeight={TYPOGRAPHY.fontWeightRegular}
                    borderRadius={BORDERS.size_two}
                  >
                    <CommandIcon command={command} />
                    <CommandText
                      command={command}
                      robotSideAnalysis={robotSideAnalysis}
                      css={COMMAND_ROW_STYLE}
                    />
                  </Flex>
                </Flex>
              )
            }}
          </ViewportList>
        </Flex>
      ) : null}
    </Flex>
  )
}
