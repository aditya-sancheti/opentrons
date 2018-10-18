// @flow
import * as React from 'react'
import {Formik} from 'formik'
import * as Yup from 'yup'
import i18n from '../../localization'
import {
  Card,
  CheckboxField,
  FormGroup,
  InputField,
  OutlineButton,
  PrimaryButton,
} from '@opentrons/components'
import styles from './LiquidEditForm.css'
import formStyles from '../forms.css'
import type {LiquidGroup} from '../../labware-ingred/types'

type Props = {
  ...$Exact<LiquidGroup>,
  deleteLiquidGroup: () => mixed,
  cancelForm: () => mixed,
  saveForm: (LiquidGroup) => mixed,
}

type LiquidEditFormValues = {
  name: string,
  description?: ?string,
  serialize?: boolean,
}
export const liquidEditFormSchema = Yup.object().shape({
  name: Yup.string().required('Name is required'),
  description: Yup.string(),
  serialize: Yup.boolean(),
})

export default function LiquidEditForm (props: Props) {
  const {deleteLiquidGroup, cancelForm, saveForm} = props

  const initialValues = {
    name: props.name,
    description: props.description || '',
    serialize: props.serialize || false,
  }

  return (
    <Formik
      initialValues={initialValues}
      validationSchema={liquidEditFormSchema}
      onSubmit={(values: LiquidEditFormValues) => saveForm({
        name: values.name,
        description: values.description || null,
        serialize: values.serialize || false,
      })}
      render={({handleChange, handleBlur, handleSubmit, dirty, errors, isValid, touched, values}) => (
        <Card className={styles.form_card}>
          <form onSubmit={handleSubmit}>
            <section className={styles.section}>
              <div className={formStyles.header}>{i18n.t('form.liquid.details')}</div>
              <div className={formStyles.row_wrapper}>
                <FormGroup
                  label={`${i18n.t('form.liquid.name')}:`}
                  className={formStyles.column_1_2}>
                  <InputField
                    name='name'
                    error={touched.name && errors.name}
                    value={values.name}
                    onChange={handleChange}
                    onBlur={handleBlur}
                  />
                </FormGroup>
                <FormGroup
                  label={`${i18n.t('form.liquid.description')}:`}
                  className={formStyles.column_1_2}>
                  <InputField
                    name='description'
                    value={values.description}
                    onChange={handleChange} />
                </FormGroup>
              </div>
            </section>

            <section className={styles.section}>
              <div className={formStyles.header}>{i18n.t('form.liquid.serialize_title')}</div>
              <p className={styles.info_text}>
                {i18n.t('form.liquid.serialize_explanation')}</p>
              <CheckboxField
                name='serialize'
                label={i18n.t('form.liquid.serialize')}
                value={values.serialize}
                onChange={handleChange} />
            </section>

            <div className={styles.button_row}>
              <OutlineButton onClick={deleteLiquidGroup}>{i18n.t('button.delete')}</OutlineButton>
              <PrimaryButton onClick={cancelForm}>{i18n.t('button.cancel')}</PrimaryButton>
              <PrimaryButton
                disabled={!dirty}
                type='submit' >
                {i18n.t('button.save')}
              </PrimaryButton>
            </div>
          </form>
        </Card>
      )}
    />
  )
}
