import * as React from 'react'
import map from 'lodash/map'

import {
  Flex,
  Box,
  LabwareRender,
  Module,
  RobotWorkSpace,
  DIRECTION_COLUMN,
  SPACING,
} from '@opentrons/components'
import {
  getDeckDefFromRobotType,
  inferModuleOrientationFromXCoordinate,
  RunTimeCommand,
  THERMOCYCLER_MODULE_V1,
} from '@opentrons/shared-data'
import { useFeatureFlag } from '../../../../redux/config'
import { ModuleExtraAttention } from '../ModuleExtraAttention'
import { LabwareInfoOverlay } from '../LabwareInfoOverlay'
import {
  useLabwareRenderInfoForRunById,
  useModuleRenderInfoForProtocolById,
  useProtocolDetailsForRun,
  useRunHasStarted,
} from '../../hooks'
import type { ModuleTypesThatRequireExtraAttention } from '../../../ProtocolSetup/RunSetupCard/LabwareSetup/utils/getModuleTypesThatRequireExtraAttention'
import { getLabwareSetupItemGroups } from './utils'
import { OffDeckLabwareList } from './OffDeckLabwareList'
import { getStandardDeckViewLayerBlockList } from '../utils/getStandardDeckViewLayerBlockList'

interface SetupLabwareMapProps {
  robotName: string
  runId: string
  commands: RunTimeCommand[]
  extraAttentionModules: ModuleTypesThatRequireExtraAttention[]
}

export function SetupLabwareMap({
  robotName,
  runId,
  extraAttentionModules,
  commands,
}: SetupLabwareMapProps): JSX.Element {
  const moduleRenderInfoById = useModuleRenderInfoForProtocolById(
    robotName,
    runId
  )
  const { robotType } = useProtocolDetailsForRun(runId)
  const labwareRenderInfoById = useLabwareRenderInfoForRunById(runId)
  const runHasStarted = useRunHasStarted(runId)
  const enableLiquidSetup = useFeatureFlag('enableLiquidSetup')

  const deckDef = getDeckDefFromRobotType(robotType)

  const { offDeckItems } = getLabwareSetupItemGroups(commands)
  return (
    <Flex flex="1" maxHeight="180vh" flexDirection={DIRECTION_COLUMN}>
      <Flex flexDirection={DIRECTION_COLUMN} marginY={SPACING.spacing4}>
        {!runHasStarted &&
        !enableLiquidSetup &&
        extraAttentionModules.length > 0 &&
        moduleRenderInfoById ? (
          <ModuleExtraAttention
            moduleTypes={extraAttentionModules}
            modulesInfo={moduleRenderInfoById}
          />
        ) : null}
        <Box margin="0 auto" maxWidth="46.25rem" width="100%">
          <RobotWorkSpace
            deckDef={deckDef}
            deckLayerBlocklist={getStandardDeckViewLayerBlockList(robotType)}
            id="LabwareSetup_deckMap"
          >
            {() => (
              <>
                {map(
                  moduleRenderInfoById,
                  ({
                    x,
                    y,
                    moduleDef,
                    nestedLabwareDef,
                    nestedLabwareId,
                    nestedLabwareDisplayName,
                  }) => (
                    <Module
                      key={`LabwareSetup_Module_${moduleDef.model}_${x}${y}`}
                      x={x}
                      y={y}
                      orientation={inferModuleOrientationFromXCoordinate(x)}
                      def={moduleDef}
                      innerProps={
                        moduleDef.model === THERMOCYCLER_MODULE_V1
                          ? { lidMotorState: 'open' }
                          : {}
                      }
                    >
                      {nestedLabwareDef != null && nestedLabwareId != null ? (
                        <React.Fragment
                          key={`LabwareSetup_Labware_${nestedLabwareDef.metadata.displayName}_${x}${y}`}
                        >
                          <LabwareRender definition={nestedLabwareDef} />
                          <LabwareInfoOverlay
                            definition={nestedLabwareDef}
                            labwareId={nestedLabwareId}
                            displayName={nestedLabwareDisplayName}
                            runId={runId}
                          />
                        </React.Fragment>
                      ) : null}
                    </Module>
                  )
                )}
                {map(
                  labwareRenderInfoById,
                  ({ x, y, labwareDef, displayName }, labwareId) => {
                    return (
                      <React.Fragment
                        key={`LabwareSetup_Labware_${labwareDef.metadata.displayName}_${x}${y}`}
                      >
                        <g transform={`translate(${x},${y})`}>
                          <LabwareRender definition={labwareDef} />
                          <LabwareInfoOverlay
                            definition={labwareDef}
                            labwareId={labwareId}
                            displayName={displayName}
                            runId={runId}
                          />
                        </g>
                      </React.Fragment>
                    )
                  }
                )}
              </>
            )}
          </RobotWorkSpace>
        </Box>
        <OffDeckLabwareList labwareItems={offDeckItems} />
      </Flex>
    </Flex>
  )
}