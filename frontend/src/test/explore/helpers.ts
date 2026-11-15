import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import Ajv2020 from 'ajv/dist/2020.js'
import addFormats from 'ajv-formats'
import { parse } from 'yaml'

const ROOT = resolve(__dirname, '../../../..')

export interface OpenApiDocument {
  paths: Record<string, unknown>
  components: { schemas: Record<string, unknown>; responses: Record<string, unknown> }
}

export const openApi = parse(readFileSync(resolve(ROOT, 'docs/openapi-contract-v0.yaml'), 'utf8')) as OpenApiDocument

/** Validador JSON Schema (2020-12) construido sobre el OpenAPI real del contrato AZ-04. */
const ajv = new Ajv2020({ strict: false, allErrors: true })
addFormats(ajv)
ajv.addSchema(openApi, 'openapi')

export function validateAgainst(schemaName: string, value: unknown): string[] {
  const validate = ajv.getSchema(`openapi#/components/schemas/${schemaName}`)
  if (!validate) throw new Error(`Esquema inexistente en el OpenAPI: ${schemaName}`)
  validate(value)
  return (validate.errors ?? []).map((error) => `${error.instancePath || '/'} ${error.message ?? ''}`)
}

/** Respuesta real observada en el backend integrado en `dev` (docs/fe-03/ejemplos-observados). */
export function observed(name: string): unknown {
  return JSON.parse(readFileSync(resolve(ROOT, `docs/fe-03/ejemplos-observados/${name}.json`), 'utf8'))
}
