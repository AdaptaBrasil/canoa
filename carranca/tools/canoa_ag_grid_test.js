/**
 * canoa_ag_grid_test.js
 * Tests of static/js/canoa_ag_grid.js, no browser needed (a fake `agGrid` and `document`).
 *
 * Usage:  node carranca/tools/canoa_ag_grid_test.js
 *
 * mgd + Anthropic Claude -- 2026-11-10 -- 2026-11-16
 */
const assert = require('node:assert/strict');
const path = require('node:path');

const CanoaAgGrid = require(path.join(__dirname, '..', 'static', 'js', 'canoa_ag_grid.js'));
const { buildColumnDefs, decodeHtmlEntities, formatters, isoDate, isoDateTime, selectionOptions } = CanoaAgGrid;

let count = 0;
const test = (name, fn) => { fn(); count++; console.log('  ok  ', name); };
const testAsync = async (name, fn) => { await fn(); count++; console.log('  ok  ', name); };

const fakeDoc = {
    createElement: () => ({
        set innerHTML(v) { this._v = v.replace('&ccedil;', 'ç').replace('&atilde;', 'ã'); },
        get value() { return this._v; },
    }),
};

// -- decodeHtmlEntities ------------------------------------------------------------------------------------
test('decode: plain text does not touch the DOM', () => {
    const boom = { createElement: () => { throw new Error('the DOM must not be used'); } };
    assert.equal(decodeHtmlEntities('Nome', boom), 'Nome');
    assert.equal(decodeHtmlEntities('a & b', boom), 'a & b');   // & without ;
    assert.equal(decodeHtmlEntities('a; b', boom), 'a; b');     // ; without &
    assert.equal(decodeHtmlEntities('', boom), '');
});
test('decode: an entity goes through the DOM; without a document it is returned as is', () => {
    assert.equal(decodeHtmlEntities('Opera&ccedil;&atilde;o', fakeDoc), 'Operação');
    assert.equal(decodeHtmlEntities('Opera&ccedil;&atilde;o', null), 'Opera&ccedil;&atilde;o');
});

// -- formats -----------------------------------------------------------------------------------------------
test('iso dates use local time and are not locale dependent', () => {
    const d = new Date(2026, 10, 7, 20, 22);  // local 2026-11-07 20:22
    assert.equal(isoDate(d), '2026-11-07');
    assert.equal(isoDateTime(d), '2026-11-07 20:22');
    assert.equal(isoDate(new Date(2026, 0, 2, 0, 5)), '2026-01-02');  // near midnight: no shift to the adjacent day
    assert.equal(isoDate(null), '');
    assert.equal(isoDateTime(''), '');
});
test('int, percent, date, datetime', () => {
    const f = formatters('pt-BR');
    assert.equal(f.int(87880), '87.880');
    assert.equal(f.int(null), '');
    assert.equal(f.percent(87.4), '87%');
    assert.equal(f.percent(undefined), '');
    assert.equal(f.date(new Date(2026, 10, 7)), '07/11/2026');
    assert.equal(f.date(''), '');
    assert.match(f.datetime(new Date(2026, 10, 7, 20, 22)), /^07\/11\/2026,? 20:22/);
});

// -- buildColumnDefs ---------------------------------------------------------------------------------------
const meta = [
    { n: 'id', h: '' },
    { n: 'name', h: 'Nome' },
    { n: 'qty', h: 'Quantidade' },
    { n: 'done_at', h: 'Opera&ccedil;&atilde;o' },
    { n: 'visible', h: 'Vis&iacute;vel' },
];
const base = { colMeta: meta, userLocale: 'pt-BR', remPx: 16, decode: t => decodeHtmlEntities(t, fakeDoc) };

test('columns: empty header is hidden, others flex 1, headers decoded', () => {
    const defs = buildColumnDefs(base);
    assert.equal(defs.length, 5);
    assert.deepEqual(defs[0], { field: 'id', headerName: '', hide: true });
    assert.deepEqual(defs[1], { field: 'name', headerName: 'Nome', flex: 1 });
    assert.equal(defs[3].headerName, 'Operação');
});
test('columns: kinds, sizing and the colDef override (merged last)', () => {
    const defs = buildColumnDefs({
        ...base,
        columns: {
            name: { flex: 4 },
            qty: { kind: 'int', width: 'header' },
            done_at: { kind: 'iso-datetime', width: '16rem', wrap: true },
            visible: { kind: 'center', colDef: { flex: 5, headerName: 'X' } },
        },
    });
    assert.equal(defs[1].flex, 4);
    assert.equal(defs[2].type, 'numericColumn');
    assert.equal(defs[2].width, 16 * 'Quantidade'.length);
    assert.equal(defs[2].maxWidth, defs[2].width);
    assert.equal(defs[2].valueFormatter({ value: 1234 }), '1.234');
    assert.equal(defs[3].width, 256);
    assert.equal(defs[3].wrapHeaderText, true);
    assert.equal(defs[3].valueFormatter({ value: new Date(2026, 10, 7, 20, 22) }), '2026-11-07 20:22');
    assert.equal(defs[4].headerClass, 'grd-header-center');
    assert.equal(defs[4].flex, 5);
    assert.equal(defs[4].headerName, 'X');
});
test('columns: hide, a px width, unknown names and kinds', () => {
    const warns = [];
    const defs = buildColumnDefs({
        ...base, warn: m => warns.push(m),
        columns: { name: { hide: true }, qty: { width: 120 }, nope: {} },
    });
    assert.deepEqual(defs.map(d => d.field), ['id', 'name', 'qty', 'done_at', 'visible']);   // colMeta order
    assert.equal(defs[1].hide, true);
    assert.equal(defs[2].width, 120);
    assert.equal(defs[2].flex, undefined);   // width or flex, never both
    assert.deepEqual(warns, ['CanoaAgGrid: [nope] is not in colMeta, ignored.']);
    assert.throws(() => buildColumnDefs({ ...base, columns: { qty: { kind: 'bogus' } } }), /unknown column kind \[bogus\]/);
});
test('columns: a colMeta column that the rows do not have is left out', () => {
    const defs = buildColumnDefs({ ...base, present: new Set(['id', 'name', 'visible']) });
    assert.deepEqual(defs.map(d => d.field), ['id', 'name', 'visible']);
    assert.equal(buildColumnDefs({ ...base, present: null }).length, 5);   // no rows: all of them
});
test('selection options: the one place of the syntax', () => {
    assert.deepEqual(selectionOptions(false), { rowSelection: 'single' });
    assert.deepEqual(selectionOptions(true), { rowSelection: 'single', suppressRowDeselection: true });
});

// -- create (fake agGrid and document) -----------------------------------------------------------------------
const fakeGrid = () => {
    const rows = [0, 1, 2].map(i => ({
        rowIndex: i, data: { id: `code${i}` }, selected: false, setSelected(v) { this.selected = v; },
    }));
    return { rows, api: { getDisplayedRowAtIndex: i => rows[i] ?? null } };
};
// the browser's own globals (fakes); the data of the grid is not a global, it is the first argument of create()
const setBrowser = () => {
    globalThis.document = { documentElement: {}, getElementById: id => ({ id }), createElement: fakeDoc.createElement };
    globalThis.getComputedStyle = () => ({ fontSize: '16px' });
    globalThis.created = null;
    globalThis.agGrid = { createGrid: (el, options) => { globalThis.created = { el, options }; return { fake: true }; } };
};
// what the layout writes as `Canoa.grid` (here, of a grid that posts its active row)
const newData = () => ({
    id: 'ag-grid-id',
    colMeta: meta,
    rows: [0, 1, 2].map(i => ({ id: `code${i}`, name: `n${i}`, qty: i, done_at: null, visible: true })),
    locale: 'pt-BR',
    colCode: 'id',
    cargoKeys: { row_index: 'row_index', code: 'code' },
    cargo: { row_index: 1, code: '' },
});

(async () => {
    await testAsync('create: the data of the grid is required', async () => {
        setBrowser();
        assert.throws(() => CanoaAgGrid.create(undefined), /the data of the grid is missing/);
        assert.equal(created, null);
    });
    await testAsync('create: restoreRow selects the row of the cargo and keeps it there', async () => {
        setBrowser();
        const data = newData();
        const { cargo } = data;
        const seen = [];
        const { api } = CanoaAgGrid.create(data, {
            restoreRow: true, keepSelected: true, onActiveRow: (row, ix) => seen.push([row.data.id, ix]),
        });
        assert.deepEqual(api, { fake: true });
        assert.equal(created.el.id, 'ag-grid-id');
        assert.equal(created.options.rowSelection, 'single');
        assert.equal(created.options.suppressRowDeselection, true);
        assert.equal(created.options.columnDefs.length, 5);

        const { rows, api: fakeApi } = fakeGrid();
        created.options.onGridReady({ api: fakeApi });
        await new Promise(r => setTimeout(r, 50));
        assert.equal(rows[1].selected, true);
        assert.deepEqual(cargo, { row_index: 1, code: 'code1' });
        assert.deepEqual(seen, [['code1', 1]]);
    });
    await testAsync('create: restoreRow without a row index in the cargo selects the first row', async () => {
        setBrowser();
        const data = newData();
        const { cargo } = data;
        delete cargo.row_index;
        CanoaAgGrid.create(data, { restoreRow: true });
        const { rows, api: fakeApi } = fakeGrid();
        created.options.onGridReady({ api: fakeApi });
        await new Promise(r => setTimeout(r, 50));
        assert.equal(rows[0].selected, true);
        assert.deepEqual(cargo, { row_index: 0, code: 'code0' });
    });
    await testAsync('create: onCellFocused tracks the active row; a null row changes nothing', async () => {
        setBrowser();
        const data = newData();
        const { cargo } = data;
        CanoaAgGrid.create(data);
        const { api: fakeApi } = fakeGrid();
        created.options.onCellFocused({ api: fakeApi, rowIndex: 2 });
        assert.deepEqual(cargo, { row_index: 2, code: 'code2' });
        created.options.onCellFocused({ api: fakeApi, rowIndex: null });
        assert.deepEqual(cargo, { row_index: 2, code: 'code2' });
    });
    await testAsync('create: a grid without cargo (read only) has no tracking, and gridOptions go last', async () => {
        setBrowser();
        const data = newData();
        delete data.cargo;
        const onSelectionChanged = () => { };
        CanoaAgGrid.create(data, { gridOptions: { onSelectionChanged, rowSelection: 'multiple' } });
        assert.equal(created.options.onCellFocused, undefined);
        assert.equal(created.options.onGridReady, undefined);
        assert.equal(created.options.onSelectionChanged, onSelectionChanged);
        assert.equal(created.options.rowSelection, 'multiple');
    });
    await testAsync('create: restoreRow without cargo uses the first row; onReady runs after', async () => {
        setBrowser();
        const data = newData();
        delete data.cargo;
        let ready = false;
        CanoaAgGrid.create(data, { restoreRow: true, onReady: () => { ready = true; } });
        const { rows, api: fakeApi } = fakeGrid();
        created.options.onGridReady({ api: fakeApi });
        await new Promise(r => setTimeout(r, 50));
        assert.equal(rows[0].selected, true);
        assert.equal(ready, true);
    });

    console.log(`\n${count} tests passed`);
})().catch(e => { console.error(e); process.exit(1); });
